"""Heartbeat manager for keeping agent status active."""

import logging
import time
import threading
from typing import Optional, TYPE_CHECKING

from .exceptions import HeartbeatError

if TYPE_CHECKING:
    from .gateway_client import GatewayClient

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """Manages periodic heartbeat signals to the API via the gateway proxy."""

    def __init__(
        self,
        gateway_client: "GatewayClient",
        agent_name: str,
        interval: int = 60
    ):
        self.gateway_client = gateway_client
        self.agent_name = agent_name
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the heartbeat thread."""
        if self._running:
            raise HeartbeatError("Heartbeat already running")

        self._running = True
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info(f"Heartbeat started for agent '{self.agent_name}'")

    def stop(self):
        """Stop the heartbeat thread."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Heartbeat stopped")

    def _heartbeat_loop(self):
        """Background loop that sends heartbeat periodically."""
        while self._running:
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat send failed: {e}", exc_info=True)

            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.interval):
                if not self._running:
                    break
                time.sleep(1)

    def _send_heartbeat(self):
        """Send a single heartbeat to the API via gateway proxy."""
        payload = {"name": self.agent_name}

        try:
            response = self.gateway_client.http_post(
                "ai-inventory",
                "/api/v1/health/heartbeat",
                json=payload,
                timeout=5.0
            )
            if response.status_code == 404:
                logger.warning(f"Agent '{self.agent_name}' not found. Re-registration may be needed.")
            elif response.status_code not in (200, 201):
                logger.warning(f"Heartbeat returned status {response.status_code}: {response.text}")
            else:
                logger.debug(f"Heartbeat sent successfully for agent '{self.agent_name}'")
        except Exception as e:
            logger.error(f"Heartbeat request failed: {e}")
            raise HeartbeatError(f"Failed to send heartbeat: {e}")
