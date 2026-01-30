"""
Event class for device events
"""

from typing import Optional
from ...enums import EventType, EventConnectionType


class Event:
    """Event data structure for device events

    This class mirrors the Java vendordep Event class, containing
    event type and additional data.
    """

    def __init__(self):
        """Initialize an empty event"""
        self.type: EventType = EventType.BeginInitialization
        self.module_id: int = 0
        self.connection_type: EventConnectionType = EventConnectionType.USB
        self.custom_type: int = 0
        self.custom_data: Optional[bytes] = None
        # Optional message from device
        self.extra_message: Optional[str] = None

    def __repr__(self) -> str:
        """String representation for debugging"""
        msg = f", message='{self.extra_message}'" if self.extra_message else ""
        return f"Event(type={self.type}, module_id={self.module_id}{msg})"

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Event: {self.type}"
