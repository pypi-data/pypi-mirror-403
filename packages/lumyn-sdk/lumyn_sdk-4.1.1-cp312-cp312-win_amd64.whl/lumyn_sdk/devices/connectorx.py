"""
ConnectorX Device class - Wraps C++ SDK for Python.

Provides the public API that examples expect while using the C++ SDK internally.
"""

from typing import List, Optional
from .connectorx_base import ConnectorXBase
from ..domain.led.led_handler import LedHandler
from ..domain.module.module_handler import ModuleHandler


class ConnectorX(ConnectorXBase):
    """
    ConnectorX device for controlling Lumyn Labs hardware.

    Supports LED control and module/sensor data.

    Example:
        cx = ConnectorX()
        if cx.connect("COM3"):
            cx.leds.set_color("zone_0", (255, 0, 0))
    """

    def __init__(self):
        """Initialize ConnectorX device."""
        super().__init__()

        # Create handlers that wrap the C++ device
        self.leds = LedHandler(self._cpp_device)
        self.modules = ModuleHandler(self._cpp_device)

        # Alias matrix to leds for matrix operations
        self.matrix = self.leds

    @property
    def led_handler(self) -> LedHandler:
        """Get LED handler (alias for .leds)."""
        return self.leds

    @property
    def module_handler(self) -> ModuleHandler:
        """Get module handler (alias for .modules)."""
        return self.modules

    def connect_uart(self, port: str, baud: int = 115200) -> bool:
        """
        Connect via UART with custom baud rate.

        Args:
            port: Serial port identifier
            baud: Baud rate (default 115200)

        Returns:
            True if connected
        """
        return self.connect(port, baud)
