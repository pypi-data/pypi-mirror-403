"""InputEvent dataclass for handling browser input events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class InputEvent:
    """Represents an input event from the browser.

    Attributes:
        id: The ID of the input element that triggered the event.
        event_type: The type of event (e.g., 'click', 'change', 'submit').
        value: The value associated with the event (if any).
        timestamp: Unix timestamp when the event occurred.
    """

    id: str
    event_type: str
    value: Any = None
    timestamp: float | None = None

    def __repr__(self) -> str:
        """Return a string representation of the event."""
        if self.value is not None:
            return (
                f"InputEvent(id={self.id!r}, "
                f"type={self.event_type!r}, value={self.value!r})"
            )
        return f"InputEvent(id={self.id!r}, type={self.event_type!r})"
