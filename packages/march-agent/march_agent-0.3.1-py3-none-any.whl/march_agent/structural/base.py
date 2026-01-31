"""Base class for structural streaming objects."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..streamer import Streamer


class StructuralStreamer(ABC):
    """Base class for structural streaming objects.

    Structural streamers generate events but don't hold streaming state.
    The Streamer binds to them via stream_by() to enable streaming.
    """

    def __init__(self, id: Optional[str] = None):
        """Initialize with auto-generated or explicit ID."""
        self.id = id or self._generate_id()
        self._streamer: Optional['Streamer'] = None

    @abstractmethod
    def _generate_id(self) -> str:
        """Generate a unique ID for this streamer type."""
        pass

    @abstractmethod
    def get_event_type_prefix(self) -> str:
        """Get the event type prefix (e.g., 'artifact', 'text_block')."""
        pass

    def _bind_streamer(self, streamer: 'Streamer') -> 'StructuralStreamer':
        """Bind this structural streamer to a Streamer instance.

        Called by Streamer.stream_by(). Returns self for chaining.
        """
        self._streamer = streamer
        return self

    def _send_event(self, action: str, **kwargs) -> 'StructuralStreamer':
        """Send an event through the bound streamer.

        Creates event payload and sends via streamer._send().
        Returns self for method chaining.
        """
        if not self._streamer:
            raise RuntimeError(
                f"{self.__class__.__name__} not bound to a Streamer. "
                f"Call streamer.stream_by() first."
            )

        # Build event body
        body = {"id": self.id, **kwargs}

        # Build event type
        event_type = f"{self.get_event_type_prefix()}:{action}"

        # Send through streamer using existing _send() method
        # content = stringified JSON body
        # eventType = structural event type
        # persist = False (structural events not persisted as content)
        import json
        self._streamer._send(
            content=json.dumps(body),
            done=False,
            persist=False,
            event_type=event_type
        )

        return self
