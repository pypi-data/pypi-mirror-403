"""
Type stubs for DirectLED - Efficient low-level LED control with delta compression.
"""

from typing import List, Tuple


class DirectLED:
    """
    DirectLED provides efficient, low-level LED control with delta compression.

    This class allows you to set individual LED colors and automatically handles
    delta compression to minimize bandwidth usage.

    Example:
        >>> direct = device.create_direct_led("zone_0", num_leds=60)
        >>> colors = [(255, 0, 0)] * 60  # All red
        >>> direct.update(colors)
    """

    zone_id: str
    num_leds: int

    def __init__(
        self,
        cpp_device,
        zone_id: str,
        num_leds: int,
        full_refresh_interval: int = 100
    ) -> None:
        """
        Initialize DirectLED for a specific zone.

        Args:
            cpp_device: The C++ SDK ConnectorXInternal instance
            zone_id: Zone identifier (e.g., "zone_0", "front_leds")
            num_leds: Number of LEDs in the zone
            full_refresh_interval: How often to force a full refresh (default: 100 frames, 0 to disable)
        """
        ...

    def update(self, colors: List[Tuple[int, int, int]]) -> bool:
        """
        Update the LEDs with new colors.

        Uses delta compression to only send changed pixels.

        Args:
            colors: List of (r, g, b) tuples, one per LED

        Returns:
            True if update was successful

        Raises:
            ValueError: If the number of colors doesn't match num_leds
        """
        ...

    def set_all(self, color: Tuple[int, int, int]) -> bool:
        """
        Set all LEDs to the same color.

        Args:
            color: (r, g, b) tuple

        Returns:
            True if successful
        """
        ...

    def clear(self) -> bool:
        """
        Turn off all LEDs (set to black).

        Returns:
            True if successful
        """
        ...

    def force_full_update(self, colors: List[Tuple[int, int, int]]) -> bool:
        """
        Force a full buffer update without delta compression.

        Useful after connection issues or to reset state.

        Args:
            colors: List of (r, g, b) tuples

        Returns:
            True if successful

        Raises:
            ValueError: If the number of colors doesn't match num_leds
        """
        ...

    def reset(self) -> None:
        """
        Reset the buffer state, forcing the next update to be full.

        Useful after reconnecting or when you suspect the device state
        is out of sync.
        """
        ...

    @property
    def frame_count(self) -> int:
        """Get the current frame count since last full refresh."""
        ...

    @property
    def full_refresh_interval(self) -> int:
        """Get the full refresh interval."""
        ...

    @full_refresh_interval.setter
    def full_refresh_interval(self, value: int) -> None:
        """Set the full refresh interval."""
        ...
