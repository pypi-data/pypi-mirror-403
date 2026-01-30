"""
Event domain package

Contains event-related classes and enums for the Lumyn SDK.
"""

# Import from enums module for consistency
from ...enums import EventType, DeviceStatus, EventConnectionType

# Import the proper Event class
from .event import Event

# Import event conversion utilities
from .event_converter import convert_cpp_event_to_python

__all__ = [
    'Event',
    'EventType',
    'DeviceStatus',
    'EventConnectionType',
    'convert_cpp_event_to_python'
]
