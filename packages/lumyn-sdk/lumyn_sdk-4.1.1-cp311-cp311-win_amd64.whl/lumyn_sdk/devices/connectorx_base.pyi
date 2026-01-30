"""
Type stubs for lumyn_sdk.devices.connectorx_base
"""

from typing import Optional

from .._bindings.config import LumynConfiguration
from ..domain.event.event import Event
from ..interfaces.i_event_callback import IEventCallback
from ..domain.led.direct_led import DirectLED
from ..domain.module.module_data_dispatcher import ModuleDataDispatcher


class ConnectorXBase:
    """
    Base class for ConnectorX devices using the C++ SDK.

    Wraps _bindings.connectorx.ConnectorXInternal to provide a Python-friendly interface.
    """

    def __init__(self) -> None:
        """Initialize the device wrapper."""
        ...

    def connect(self, port: str, baudrate: Optional[int] = None) -> bool:
        """
        Connect to device via serial port.

        Args:
            port: Serial port (e.g., "COM3" or "/dev/ttyUSB0")
            baudrate: Optional baud rate (defaults to device default)

        Returns:
            True if connected successfully
        """
        ...

    def connect_usb(self, port: str) -> bool:
        """
        Connect via USB (alias for connect with default baud).

        Args:
            port: Serial port identifier

        Returns:
            True if connected successfully
        """
        ...

    def disconnect(self) -> None:
        """Disconnect from the device."""
        ...

    def close(self) -> None:
        """Close the device connection (alias for disconnect)."""
        ...

    def is_connected(self) -> bool:
        """Check if device is connected."""
        ...

    def on_connected(self) -> None:
        """Hook called after successful connection. Override in subclasses."""
        ...

    # Configuration methods

    def request_config(self, timeout_ms: int = 5000) -> Optional[LumynConfiguration]:
        """
        Request configuration from device.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            LumynConfiguration object or None if failed
        """
        ...

    def apply_configuration_json(self, config_json: str) -> bool:
        """
        Apply configuration from JSON string.

        Args:
            config_json: JSON configuration

        Returns:
            True if successful
        """
        ...

    def load_configuration_from_file(self, file_path: str) -> bool:
        """
        Load and apply configuration from JSON file.

        Args:
            file_path: Path to JSON config file

        Returns:
            True if successful
        """
        ...

    # Event handling

    def add_event_callback(self, callback: IEventCallback) -> None:
        """Register an event callback."""
        ...

    def remove_event_callback(self, callback: IEventCallback) -> None:
        """Unregister an event callback."""
        ...

    def set_auto_poll_events(self, enabled: bool) -> None:
        """Enable/disable automatic event polling."""
        ...

    def poll_events_once(self) -> None:
        """Poll for events once and notify callbacks."""
        ...

    # Module dispatcher

    def get_module_dispatcher(self) -> ModuleDataDispatcher:
        """Get the module data dispatcher for registering module listeners.

        Returns:
            ModuleDataDispatcher instance for polling module data
        """
        ...

    # Direct LED

    def create_direct_led(self, zone_id: str, num_leds: int, full_refresh_interval: int = 100) -> DirectLED:
        """Create a DirectLED instance for low-level LED control.

        Args:
            zone_id: Zone identifier (e.g., "zone_0", "front_leds")
            num_leds: Number of LEDs in the zone
            full_refresh_interval: How often to force full refresh (default: 100 frames)

        Returns:
            DirectLED instance for efficient pixel-level control
        """
        ...

    # Internal access

    def _get_cpp_device(self): ...
    def _get_command_handler(self): ...
