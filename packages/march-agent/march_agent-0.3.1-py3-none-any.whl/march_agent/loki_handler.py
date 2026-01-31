"""
Loki log handler for remote log collection.

This module provides a Python logging.Handler that batches logs
and sends them to a centralized Loki instance via the agent-gateway.
"""

import atexit
import gzip
import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from .gateway_client import GatewayClient

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """A single log entry to be sent to Loki."""
    timestamp: int  # Unix timestamp in nanoseconds
    level: str
    message: str
    extra: Dict[str, str] = field(default_factory=dict)


class LokiLogHandler(logging.Handler):
    """
    A logging handler that batches and sends logs to Loki via the agent-gateway.

    Features:
    - Batches logs to reduce HTTP overhead
    - Background thread for non-blocking log sending
    - Graceful degradation when Loki is unavailable
    - Bounded buffer to prevent memory exhaustion

    Example:
        from march_agent.loki_handler import LokiLogHandler

        handler = LokiLogHandler(
            gateway_client=gateway_client,
            agent_name="my-agent",
            batch_size=100,
            flush_interval=5.0,
        )

        # Add to root logger or specific logger
        logging.getLogger().addHandler(handler)
    """

    def __init__(
        self,
        gateway_client: "GatewayClient",
        agent_name: str,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_buffer_size: int = 10000,
        retry_max_delay: float = 30.0,
        level: int = logging.DEBUG,
        enable_compression: bool = True,
    ):
        """
        Initialize the Loki log handler.

        Args:
            gateway_client: The GatewayClient for HTTP communication
            agent_name: Name of the agent (used as a label in Loki)
            batch_size: Number of logs to batch before sending (default: 100)
            flush_interval: Maximum seconds between flushes (default: 5.0)
            max_buffer_size: Maximum logs to buffer (default: 10000)
            retry_max_delay: Maximum retry delay in seconds (default: 30.0)
            level: Minimum log level to handle (default: DEBUG)
            enable_compression: Use gzip compression for log batches (default: True)
        """
        super().__init__(level=level)

        self.gateway_client = gateway_client
        self.agent_name = agent_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size
        self.retry_max_delay = retry_max_delay
        self.enable_compression = enable_compression

        # Environment-based log level override for production
        if os.getenv("ENVIRONMENT") == "production":
            production_level = max(level, logging.INFO)
            self.setLevel(production_level)
            if production_level != level:
                logger.info(f"Production mode: Elevated log level from {level} to {production_level}")

        # Thread-safe queue for log entries
        self._queue: queue.Queue[LogEntry] = queue.Queue(maxsize=max_buffer_size)

        # Background flush thread
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Retry state
        self._retry_delay = 1.0
        self._last_error_time: Optional[float] = None

        # Start background thread
        self._start_flush_thread()

        # Register cleanup on exit
        atexit.register(self.close)

    def _start_flush_thread(self):
        """Start the background flush thread."""
        with self._lock:
            if self._running:
                return

            self._running = True
            self._thread = threading.Thread(
                target=self._flush_loop,
                daemon=True,
                name=f"LokiLogHandler-{self.agent_name}"
            )
            self._thread.start()

    def _flush_loop(self):
        """Background loop that periodically flushes logs."""
        last_flush = time.time()

        while self._running:
            try:
                # Calculate time until next flush
                elapsed = time.time() - last_flush
                wait_time = max(0, self.flush_interval - elapsed)

                # Try to collect logs up to batch_size or until timeout
                entries: List[LogEntry] = []
                deadline = time.time() + wait_time

                while len(entries) < self.batch_size:
                    remaining = max(0, deadline - time.time())
                    if remaining <= 0 and entries:
                        break

                    try:
                        entry = self._queue.get(timeout=min(remaining, 0.5) if remaining > 0 else 0.1)
                        entries.append(entry)
                        self._queue.task_done()
                    except queue.Empty:
                        if time.time() >= deadline:
                            break

                # Flush if we have entries
                if entries:
                    self._flush_entries(entries)
                    last_flush = time.time()

            except Exception as e:
                # Log locally but don't crash
                logger.warning(f"Error in Loki flush loop: {e}")
                time.sleep(1.0)

    def _flush_entries(self, entries: List[LogEntry]):
        """Send a batch of log entries to Loki via the gateway."""
        if not entries:
            return

        payload = {
            "agent_name": self.agent_name,
            "entries": [
                {
                    "timestamp": e.timestamp,
                    "level": e.level,
                    "message": e.message,
                    "extra": e.extra,
                }
                for e in entries
            ]
        }

        try:
            # Prepare headers
            headers = {"X-API-Key": self.gateway_client.api_key}

            # Prepare body (with optional compression)
            json_payload = json.dumps(payload).encode('utf-8')
            body = json_payload

            if self.enable_compression:
                body = gzip.compress(json_payload)
                headers["Content-Encoding"] = "gzip"
                headers["Content-Type"] = "application/json"
            else:
                headers["Content-Type"] = "application/json"

            # Use gateway client's HTTP URL
            response = requests.post(
                f"{self._get_http_url()}/api/v1/logs",
                data=body,
                headers=headers,
                timeout=10.0,
            )

            if response.status_code in (200, 204):
                # Success - reset retry delay
                self._retry_delay = 1.0
                self._last_error_time = None
            else:
                raise Exception(f"Gateway returned status {response.status_code}")

        except Exception as e:
            # Log warning locally (but avoid recursion by using direct stderr)
            current_time = time.time()
            if self._last_error_time is None or current_time - self._last_error_time > 60:
                import sys
                print(
                    f"[LokiLogHandler] Failed to send {len(entries)} logs: {e}. "
                    f"Retry delay: {self._retry_delay}s",
                    file=sys.stderr
                )
                self._last_error_time = current_time

            # Exponential backoff
            time.sleep(self._retry_delay)
            self._retry_delay = min(self._retry_delay * 2, self.retry_max_delay)

            # Re-queue entries that failed (if buffer has space)
            for entry in entries:
                try:
                    self._queue.put_nowait(entry)
                except queue.Full:
                    break  # Buffer full, drop oldest logs

    def _get_http_url(self) -> str:
        """Get HTTP URL from gateway client (handles protocol conversion)."""
        if hasattr(self.gateway_client, 'http_url'):
            return self.gateway_client.http_url

        # Fallback: convert gRPC URL to HTTP URL
        gateway_url = self.gateway_client.gateway_url
        return gateway_url.replace("grpc://", "http://").replace("grpcs://", "https://")

    def is_healthy(self) -> bool:
        """
        Check if handler is functioning (not backlogged).

        Returns:
            True if handler is running and buffer is not >80% full
        """
        return (
            self._running and
            self._queue.qsize() < self.max_buffer_size * 0.8
        )

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record.

        This method is called by the logging framework for each log message.
        It converts the record to a LogEntry and queues it for sending.
        """
        try:
            # Convert LogRecord to LogEntry
            entry = self._record_to_entry(record)

            # Try to add to queue (non-blocking)
            try:
                self._queue.put_nowait(entry)
            except queue.Full:
                # Buffer full - drop this log (graceful degradation)
                pass

        except Exception:
            # Never crash due to logging
            self.handleError(record)

    def _record_to_entry(self, record: logging.LogRecord) -> LogEntry:
        """Convert a logging.LogRecord to a LogEntry."""
        # Get timestamp in nanoseconds
        timestamp = int(record.created * 1_000_000_000)

        # Normalize level name
        level = record.levelname.lower()
        if level == "warning":
            level = "warn"

        # Format message
        message = self.format(record) if self.formatter else record.getMessage()

        # Extract extra fields
        extra: Dict[str, str] = {}

        # Check for conversation_id in record
        if hasattr(record, "conversation_id"):
            extra["conversation_id"] = str(record.conversation_id)

        # Check for user_id in record
        if hasattr(record, "user_id"):
            extra["user_id"] = str(record.user_id)

        # Include logger name
        extra["logger"] = record.name

        # Include module/function info for debugging
        if record.funcName and record.funcName != "<module>":
            extra["function"] = record.funcName

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            extra["exception_type"] = record.exc_info[0].__name__

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            extra=extra,
        )

    def flush(self):
        """Flush all buffered logs immediately."""
        entries: List[LogEntry] = []
        while True:
            try:
                entry = self._queue.get_nowait()
                entries.append(entry)
                self._queue.task_done()
            except queue.Empty:
                break

        if entries:
            self._flush_entries(entries)

    def close(self):
        """Close the handler and flush remaining logs."""
        with self._lock:
            if not self._running:
                return

            self._running = False

        # Wait for flush thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        # Final flush
        self.flush()

        super().close()
