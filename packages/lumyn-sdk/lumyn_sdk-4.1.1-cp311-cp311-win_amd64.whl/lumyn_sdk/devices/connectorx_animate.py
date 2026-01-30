"""
ConnectorXAnimate Device class - LED-only variant using C++ SDK.
"""

from .connectorx_base import ConnectorXBase
from ..domain.led.led_handler import LedHandler


class ConnectorXAnimate(ConnectorXBase):
    """
    ConnectorXAnimate device - LED-only variant (no module support).

    Optimized for pure LED control applications.

    Example:
        cx = ConnectorXAnimate()
        if cx.connect_usb("COM3"):
            cx.leds.set_color("matrix_display", (0, 255, 0))
    """

    def __init__(self):
        """Initialize ConnectorXAnimate device."""
        super().__init__()

        # Create LED handler
        self.leds = LedHandler(self._cpp_device)

    @property
    def led_handler(self) -> LedHandler:
        """Get LED handler (alias for .leds)."""
        return self.leds

    def __init__(self):
        """Create a new ConnectorXAnimate instance and initialize the LED handler."""
        super().__init__()

        # Create LED handler
        self.leds = LedHandler(self._get_command_handler())

    def on_connected(self) -> None:
        """
        Called after successful connection(no additional setup needed).
        """
        super().on_connected()

    def close(self) -> None:
        """Close the connection and clean up resources."""
        super().close()
