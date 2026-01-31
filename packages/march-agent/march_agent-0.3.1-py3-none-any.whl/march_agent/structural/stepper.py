"""Stepper structural streamer for multi-step progress indicators."""

from typing import Optional, List
from .base import StructuralStreamer
import uuid


class Stepper(StructuralStreamer):
    """Manages multi-step progress indicator.

    Stepper events are NOT persisted to database.
    IDs are auto-generated - no need to provide them manually.

    Example:
        stepper = Stepper(steps=["Fetch", "Process", "Report"])  # ID auto-generated
        s.stream_by(stepper).start_step(0)
        s.stream_by(stepper).complete_step(0)
        s.stream_by(stepper).start_step(1)
        s.stream_by(stepper).add_step("Verify")  # Dynamic step
        s.stream_by(stepper).complete_step(1)
        s.stream_by(stepper).done()
    """

    def __init__(
        self,
        id: Optional[str] = None,
        steps: Optional[List[str]] = None
    ):
        super().__init__(id)
        self.steps = steps or []
        self._initialized = False

    def _generate_id(self) -> str:
        return f"stepper-{uuid.uuid4().hex[:8]}"

    def get_event_type_prefix(self) -> str:
        return "stepper"

    def _ensure_initialized(self) -> 'Stepper':
        """Send initialization event with steps if not already sent.

        This is automatically called before any other stepper event.
        """
        if not self._initialized and self.steps:
            self._send_event("init", steps=self.steps)
            self._initialized = True
        return self

    def start_step(self, index: int) -> 'Stepper':
        """Mark step as in progress.

        Args:
            index: Step index to start

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        return self._send_event("start_step", index=index)

    def complete_step(self, index: int) -> 'Stepper':
        """Mark step as complete.

        Args:
            index: Step index to complete

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        return self._send_event("complete_step", index=index)

    def fail_step(self, index: int, error: Optional[str] = None) -> 'Stepper':
        """Mark step as failed.

        Args:
            index: Step index that failed
            error: Optional error message

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        kwargs = {"index": index}
        if error:
            kwargs["error"] = error
        return self._send_event("fail_step", **kwargs)

    def add_step(self, label: str, index: Optional[int] = None) -> 'Stepper':
        """Add a new step dynamically.

        Args:
            label: Step label
            index: Optional position to insert at

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        kwargs = {"label": label}
        if index is not None:
            kwargs["index"] = index
        return self._send_event("add_step", **kwargs)

    def update_step_label(self, index: int, label: str) -> 'Stepper':
        """Update step label.

        Args:
            index: Step index to update
            label: New label

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        return self._send_event("update_step_label", index=index, label=label)

    def done(self) -> 'Stepper':
        """Mark stepper as complete (all steps finished).

        Returns:
            self for method chaining
        """
        self._ensure_initialized()
        return self._send_event("done")
