"""
Type stubs for lumyn_sdk.devices.connectorx_animate
"""

from .connectorx_base import ConnectorXBase
from ..domain.led.led_handler import LedHandler


class ConnectorXAnimate(ConnectorXBase):
    """
    ConnectorXAnimate is a USB-only device wrapper that exposes the LED handler
    APIs. This class provides convenience access to the device's LED builders and
    runtime control.

    This is a simplified device class that only supports LED operations.
    It does not support:
    - UART connections (USB only)
    - Module/sensor data
    - Module handlers

    For full-featured devices with module support, use ConnectorX.
    """

    leds: LedHandler

    def __init__(self) -> None:
        """Create a new ConnectorXAnimate instance and initialize the LED handler."""
        ...

    def on_connected(self) -> None:
        """
        Called after successful connection (no additional setup needed).
        """
        ...

    def close(self) -> None:
        """Close the connection and clean up resources."""
        ...
