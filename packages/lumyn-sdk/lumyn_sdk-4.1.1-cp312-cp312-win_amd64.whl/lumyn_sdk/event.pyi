"""
Minimal type stub for lumyn_sdk.event
"""
from typing import Any


class EventType:
    BeginInitialization: int
    FinishInitialization: int
    Enabled: int
    Disabled: int
    Connected: int
    Disconnected: int
    Error: int
    FatalError: int


class Event:
    type: EventType
    data: Any
    def __init__(self) -> None: ...


Event = Event
