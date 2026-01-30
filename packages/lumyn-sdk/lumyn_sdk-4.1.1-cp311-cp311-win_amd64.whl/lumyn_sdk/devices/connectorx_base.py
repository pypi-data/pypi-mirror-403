"""
ConnectorXBase - Base class wrapping C++ SDK ConnectorX device.

This provides a Python-friendly wrapper around the C++ SDK's ConnectorXInternal class
while maintaining the public API that examples expect.
"""

from typing import TYPE_CHECKING, Optional, List, Callable
import threading
import time

from ..interfaces.i_event_callback import IEventCallback
from ..domain.event import Event, convert_cpp_event_to_python

if TYPE_CHECKING:
    from .._bindings.config import LumynConfiguration


class ConnectorXBase:
    """
    Base class for ConnectorX devices using the C++ SDK.

    Wraps _bindings.connectorx.ConnectorXInternal to provide a Python-friendly interface.
    """

    def __init__(self):
        """Initialize the device wrapper."""
        from .._bindings.connectorx import ConnectorXInternal
        from ..domain.module.module_data_dispatcher import ModuleDataDispatcher

        # C++ SDK device instance
        self._cpp_device = ConnectorXInternal()
        # Expose as _internal for tests that check for it
        self._internal = self._cpp_device

        # Module data dispatcher (pure Python implementation)
        self._module_dispatcher = ModuleDataDispatcher(self._internal)

        # Event handling
        self._event_handlers: List[IEventCallback] = []
        self._auto_poll_events = True
        self._poll_events = False
        self._polling_thread: Optional[threading.Thread] = None

        # Connection state
        self._is_connected = False

    def connect(self, port: str, baudrate: Optional[int] = None) -> bool:
        """
        Connect to device via serial port.

        Args:
            port: Serial port (e.g., "COM3" or "/dev/ttyUSB0")
            baudrate: Optional baud rate (defaults to device default)

        Returns:
            True if connected successfully
        """
        try:
            # Connect using C++ SDK
            result = self._cpp_device.Connect(port, baudrate)
            if result:
                self._is_connected = True

                # Start event polling if enabled
                if self._auto_poll_events:
                    self._start_event_polling()

                # Call subclass hook
                self.on_connected()

                return result
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def connect_usb(self, port: str) -> bool:
        """
        Connect via USB (alias for connect with default baud).

        Args:
            port: Serial port identifier

        Returns:
            True if connected successfully
        """
        return self.connect(port)

    def disconnect(self) -> None:
        """Disconnect from the device."""
        # Stop event polling
        self._stop_event_polling()

        # Stop module dispatcher
        if self._module_dispatcher:
            self._module_dispatcher.stop()

        # Disconnect C++ device
        if self._cpp_device:
            self._cpp_device.Disconnect()

        self._is_connected = False

    def close(self) -> None:
        """Close the device connection (alias for disconnect)."""
        self.disconnect()

    def is_connected(self) -> bool:
        """Check if device is connected."""
        if self._cpp_device:
            return self._cpp_device.IsConnected()
        return False

    def on_connected(self) -> None:
        """Hook called after successful connection. Override in subclasses."""
        pass

    # Configuration methods

    def request_config(self, timeout_ms: int = 5000) -> Optional["LumynConfiguration"]:
        """
        Request configuration from device.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            LumynConfiguration object or None if failed
        """
        from .. import ParseConfig
        if self._cpp_device:
            config_json = self._cpp_device.RequestConfig(timeout_ms)
            if config_json:
                return ParseConfig(config_json)
        return None

    def apply_configuration_json(self, config_json: str) -> bool:
        """
        Apply configuration from JSON string.

        Args:
            config_json: JSON configuration

        Returns:
            True if successful
        """
        if self._cpp_device:
            try:
                self._cpp_device.ApplyConfigurationJson(config_json)
                return True
            except Exception:
                return False
        return False

    def load_configuration_from_file(self, file_path: str) -> bool:
        """
        Load and apply configuration from JSON file.

        Args:
            file_path: Path to JSON config file

        Returns:
            True if successful
        """
        if self._cpp_device:
            try:
                self._cpp_device.LoadConfigurationFromFile(file_path)
                return True
            except Exception:
                return False
        return False

    # Event handling

    def add_event_callback(self, callback: IEventCallback) -> None:
        """Register an event callback."""
        if callback not in self._event_handlers:
            self._event_handlers.append(callback)

    def remove_event_callback(self, callback: IEventCallback) -> None:
        """Unregister an event callback."""
        if callback in self._event_handlers:
            self._event_handlers.remove(callback)

    def set_auto_poll_events(self, enabled: bool) -> None:
        """Enable/disable automatic event polling."""
        self._auto_poll_events = enabled
        if self._cpp_device:
            self._cpp_device.SetAutoPollEvents(enabled)

        if enabled and self._is_connected and not self._poll_events:
            self._start_event_polling()
        elif not enabled and self._poll_events:
            self._stop_event_polling()

    def poll_events_once(self) -> None:
        """Poll for events once and notify callbacks."""
        if not self._cpp_device:
            return

        try:
            # Get events from C++ SDK
            events = self._cpp_device.GetEvents()

            # Notify callbacks
            for event_data in events:
                event = convert_cpp_event_to_python(event_data)
                if event:
                    for handler in self._event_handlers:
                        try:
                            handler.handle_event(event)
                        except Exception as e:
                            print(f"Event handler error: {e}")
        except Exception as e:
            print(f"Poll events error: {e}")

    def _start_event_polling(self) -> None:
        """Start background event polling thread."""
        if self._poll_events:
            return

        self._poll_events = True
        self._polling_thread = threading.Thread(
            target=self._event_polling_loop,
            daemon=True,
            name="EventPolling"
        )
        self._polling_thread.start()

    def _stop_event_polling(self) -> None:
        """Stop background event polling thread."""
        self._poll_events = False
        if self._polling_thread:
            self._polling_thread.join(timeout=1.0)
            self._polling_thread = None

    def _event_polling_loop(self) -> None:
        """Background thread that polls for events."""
        while self._poll_events and self._is_connected:
            try:
                self.poll_events_once()
                time.sleep(0.01)  # 100Hz polling
            except Exception as e:
                print(f"Event polling loop error: {e}")
                break

    # Internal access for handlers

    def _get_cpp_device(self):
        """Get the underlying C++ device instance (for handlers)."""
        return self._cpp_device

    def _get_command_handler(self):
        """Get the command handler from the C++ device (for tests)."""
        if self._cpp_device:
            return self._cpp_device
        return None

    def get_module_dispatcher(self):
        """Get the module data dispatcher for registering module listeners.

        Returns:
            ModuleDataDispatcher instance for polling module data
        """
        return self._module_dispatcher

    def create_direct_led(self, zone_id: str, num_leds: int, full_refresh_interval: int = 100):
        """Create a DirectLED instance for low-level LED control.

        Args:
            zone_id: Zone identifier (e.g., "zone_0", "front_leds")
            num_leds: Number of LEDs in the zone
            full_refresh_interval: How often to force full refresh (default: 100 frames)

        Returns:
            DirectLED instance for efficient pixel-level control
        """
        from ..domain.led.direct_led import DirectLED
        return DirectLED(self._cpp_device, zone_id, num_leds, full_refresh_interval)
