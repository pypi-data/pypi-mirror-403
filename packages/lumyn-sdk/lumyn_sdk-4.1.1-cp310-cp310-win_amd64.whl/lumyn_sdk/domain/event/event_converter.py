"""
Event conversion utilities for converting C++ SDK events to Python events.
"""

from typing import Optional
from .event import Event
from ...enums import EventType, EventConnectionType


# Event type integer values (match LUMYN_EVENT_* constants)
_EVENT_TYPE_MAP = {
    0x00: EventType.BeginInitialization,
    0x01: EventType.FinishInitialization,
    0x02: EventType.Enabled,
    0x04: EventType.Disabled,
    0x08: EventType.Connected,
    0x10: EventType.Disconnected,
    0x20: EventType.Error,
    0x40: EventType.FatalError,
    0x80: EventType.RegisteredEntity,
    0x100: EventType.Custom,
    0x200: EventType.PinInterrupt,
    0x400: EventType.HeartBeat,
}

# Connection type integer values (match LUMYN_CONNECTION_* constants)
_CONNECTION_TYPE_MAP = {
    0: EventConnectionType.USB,
    1: EventConnectionType.WEB_USB,
    2: EventConnectionType.I2C,
    3: EventConnectionType.CAN,
    4: EventConnectionType.UART,
}


def convert_cpp_event_to_python(event_data) -> Optional[Event]:
    """Convert C++ Event to Python Event

    Args:
        event_data: C++ Event object from bindings (lumyn::internal::Eventing::Event)
                   OR dict from new GetEvents() binding

    Returns:
        Python Event object or None if conversion fails
    """
    try:
        # Handle new dict format from GetEvents binding
        if isinstance(event_data, dict):
            return _convert_dict_event_to_python(event_data)

        # Handle old C++ object format (for backward compatibility)
        return _convert_cpp_object_event_to_python(event_data)

    except Exception as e:
        print(f"Event conversion error: {e}")
        import traceback
        traceback.print_exc()
        return None


def _convert_dict_event_to_python(event_dict: dict) -> Optional[Event]:
    """Convert event dict from new GetEvents binding to Python Event.

    Args:
        event_dict: Dict with 'type', 'data', and optional 'extra_message' keys

    Returns:
        Python Event object
    """
    event = Event()

    # Get event type
    event_type_int = event_dict.get('type', 0)
    event.type = _EVENT_TYPE_MAP.get(
        event_type_int, EventType.BeginInitialization)

    # Get event data
    data = event_dict.get('data', {})

    if event.type == EventType.Connected:
        conn_type = data.get('connection_type', 0)
        event.connection_type = _CONNECTION_TYPE_MAP.get(
            conn_type, EventConnectionType.USB)

    elif event.type == EventType.Disconnected:
        conn_type = data.get('connection_type', 0)
        event.connection_type = _CONNECTION_TYPE_MAP.get(
            conn_type, EventConnectionType.USB)

    elif event.type == EventType.Disabled:
        event.custom_type = data.get('cause', 0)

    elif event.type == EventType.Error:
        event.custom_type = data.get('error_type', 0)
        msg = data.get('message', '')
        if msg:
            event.custom_data = msg.encode(
                'utf-8') if isinstance(msg, str) else msg

    elif event.type == EventType.FatalError:
        event.custom_type = data.get('fatal_error_type', 0)
        msg = data.get('message', '')
        if msg:
            event.custom_data = msg.encode(
                'utf-8') if isinstance(msg, str) else msg

    elif event.type == EventType.RegisteredEntity:
        event.module_id = data.get('entity_id', 0)

    elif event.type == EventType.Custom:
        event.custom_type = data.get('custom_type', 0)
        event.custom_data = data.get('custom_data')

    elif event.type == EventType.HeartBeat:
        # Pack status flags
        status_flags = 0
        if data.get('enabled'):
            status_flags |= 0x01
        if data.get('connected_usb'):
            status_flags |= 0x02
        if data.get('can_ok'):
            status_flags |= 0x04
        event.custom_type = status_flags

    elif event.type == EventType.PinInterrupt:
        event.custom_type = data.get('pin', 0)

    # Extra message - store in dedicated field
    extra_msg = event_dict.get('extra_message')
    if extra_msg:
        event.extra_message = extra_msg if isinstance(
            extra_msg, str) else extra_msg.decode('utf-8', errors='replace')

    return event


def _convert_cpp_object_event_to_python(event_data) -> Optional[Event]:
    """Convert old C++ Event object to Python Event (backward compatibility)."""
    from lumyn_sdk._bindings import event as event_types

    event = Event()

    # Get event type from header
    cpp_event_type = event_data.header.type
    event.type = _convert_event_type(cpp_event_type)

    # Extract data based on event type
    if cpp_event_type == event_types.EventType.Connected:
        conn_info = event_data.header.data.connected
        event.connection_type = _convert_connection_type(conn_info.type)

    elif cpp_event_type == event_types.EventType.Disconnected:
        disconn_info = event_data.header.data.disconnected
        event.connection_type = _convert_connection_type(disconn_info.type)

    elif cpp_event_type == event_types.EventType.Error:
        error_info = event_data.header.data.error
        # Store error message in custom_data
        if hasattr(error_info, 'message'):
            event.custom_data = error_info.message.encode(
                'utf-8') if isinstance(error_info.message, str) else error_info.message
        # Store error type in custom_type
        event.custom_type = int(error_info.type)

    elif cpp_event_type == event_types.EventType.FatalError:
        fatal_info = event_data.header.data.fatalError
        # Store fatal error message in custom_data
        if hasattr(fatal_info, 'message'):
            event.custom_data = fatal_info.message.encode(
                'utf-8') if isinstance(fatal_info.message, str) else fatal_info.message
        # Store fatal error type in custom_type
        event.custom_type = int(fatal_info.type)

    elif cpp_event_type == event_types.EventType.RegisteredEntity:
        entity_info = event_data.header.data.registeredEntity
        event.module_id = entity_info.id

    elif cpp_event_type == event_types.EventType.Custom:
        custom_info = event_data.header.data.custom
        event.custom_type = custom_info.type
        if hasattr(custom_info, 'data'):
            event.custom_data = custom_info.data

    elif cpp_event_type == event_types.EventType.HeartBeat:
        # HeartBeat doesn't map directly but we can store status info in custom_type
        heartbeat_info = event_data.header.data.heartBeat
        # Pack status flags into custom_type as bitmask
        status_flags = 0
        if hasattr(heartbeat_info, 'enabled') and heartbeat_info.enabled:
            status_flags |= 0x01
        if hasattr(heartbeat_info, 'connectedUSB') and heartbeat_info.connectedUSB:
            status_flags |= 0x02
        if hasattr(heartbeat_info, 'canOK') and heartbeat_info.canOK:
            status_flags |= 0x04
        event.custom_type = status_flags

    # Extract extra message if present
    if event_data.hasExtraMessage():
        extra_msg = event_data.getExtraMessage()
        if extra_msg and not event.custom_data:
            event.custom_data = extra_msg

    return event


def _convert_event_type(cpp_event_type) -> EventType:
    """Convert C++ event type to Python EventType enum

    Args:
        cpp_event_type: C++ EventType enum value (lumyn::internal::Eventing::EventType)

    Returns:
        Python EventType enum value

    Note: The C++ and Python EventType enums are identical, so this is a direct mapping.
    """
    from lumyn_sdk._bindings import event as event_types

    # Direct mapping since Python EventType now matches C++ EventType exactly
    EVENT_TYPE_MAP = {
        event_types.EventType.BeginInitialization: EventType.BeginInitialization,
        event_types.EventType.FinishInitialization: EventType.FinishInitialization,
        event_types.EventType.Enabled: EventType.Enabled,
        event_types.EventType.Disabled: EventType.Disabled,
        event_types.EventType.Connected: EventType.Connected,
        event_types.EventType.Disconnected: EventType.Disconnected,
        event_types.EventType.Error: EventType.Error,
        event_types.EventType.FatalError: EventType.FatalError,
        event_types.EventType.RegisteredEntity: EventType.RegisteredEntity,
        event_types.EventType.Custom: EventType.Custom,
        event_types.EventType.PinInterrupt: EventType.PinInterrupt,
        event_types.EventType.HeartBeat: EventType.HeartBeat,
    }

    return EVENT_TYPE_MAP.get(cpp_event_type, EventType.BeginInitialization)


def _convert_connection_type(cpp_conn_type) -> EventConnectionType:
    """Convert C++ connection type to Python EventConnectionType enum

    Args:
        cpp_conn_type: C++ ConnectionType enum value (lumyn::internal::Eventing::ConnectionType)

    Returns:
        Python EventConnectionType enum value
    """
    from lumyn_sdk._bindings import event as event_types

    # Mapping from C++ ConnectionType to Python EventConnectionType
    CONNECTION_TYPE_MAP = {
        event_types.ConnectionType.USB: EventConnectionType.USB,
        event_types.ConnectionType.WebUSB: EventConnectionType.WEB_USB,
        event_types.ConnectionType.I2C: EventConnectionType.I2C,
        event_types.ConnectionType.CAN: EventConnectionType.CAN,
        event_types.ConnectionType.UART: EventConnectionType.UART,
    }

    return CONNECTION_TYPE_MAP.get(cpp_conn_type, EventConnectionType.USB)
