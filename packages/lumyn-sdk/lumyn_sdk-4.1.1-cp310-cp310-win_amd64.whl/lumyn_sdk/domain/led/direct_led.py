"""
DirectLED - Efficient low-level LED control with delta compression.

Provides direct pixel-level control while benefiting from automatic delta
compression for optimal bandwidth usage.
"""

from typing import List, Tuple, Optional, Union


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

    def __init__(self, cpp_device, zone_id: str, num_leds: int, full_refresh_interval: int = 100):
        """
        Initialize DirectLED for a specific zone.

        Args:
            cpp_device: The C++ SDK ConnectorXInternal instance
            zone_id: Zone identifier (e.g., "zone_0", "front_leds")
            num_leds: Number of LEDs in the zone
            full_refresh_interval: How often to force a full refresh (default: 100 frames, 0 to disable)
        """
        from lumyn_sdk._bindings import led

        self._cpp_device = cpp_device
        self.zone_id = zone_id
        self.num_leds = num_leds

        # Create DirectBufferManager for automatic delta compression
        # Buffer length = num_leds * 3 (RGB bytes per LED)
        buffer_length = num_leds * 3
        self._buffer_manager = led.DirectBufferManager(
            zone_id, buffer_length, full_refresh_interval)

    def update(self, colors: Union[bytes, bytearray, List[Tuple[int, int, int]]]) -> bool:
        """
        Update the LEDs with new colors.

        Uses delta compression to only send changed pixels.

        Args:
            colors: Either raw bytes (RGB, 3 bytes per LED) or list of (r, g, b) tuples

        Returns:
            True if update was successful

        Raises:
            ValueError: If the buffer size doesn't match expected size
        """
        # Handle raw bytes input
        if isinstance(colors, (bytes, bytearray)):
            expected_bytes = self.num_leds * 3
            if len(colors) != expected_bytes:
                raise ValueError(
                    f"Expected {expected_bytes} bytes ({self.num_leds} LEDs * 3), got {len(colors)}")
            buffer = bytes(colors)
        else:
            # Handle list of tuples
            if len(colors) != self.num_leds:
                raise ValueError(
                    f"Expected {self.num_leds} colors, got {len(colors)}")

            # Convert list of RGB tuples to flat byte array
            buffer = bytearray()
            for r, g, b in colors:
                buffer.append(r & 0xFF)
                buffer.append(g & 0xFF)
                buffer.append(b & 0xFF)
            buffer = bytes(buffer)

        # Get compressed command from buffer manager
        command_bytes = self._buffer_manager.update(bytes(buffer))

        if not command_bytes:
            return False

        # Send the command to the device using SendRawCommand
        if self._cpp_device:
            try:
                # Check connection before calling C++ methods
                # (C++ SDK may abort/crash on some platforms when called unconnected)
                if hasattr(self._cpp_device, 'IsConnected') and not self._cpp_device.IsConnected():
                    return False

                # Note: DirectBufferManager.update() returns the full LED command bytes
                # (header + payload already combined), so we use SendRawCommand to send them as-is
                self._cpp_device.SendRawCommand(command_bytes)
                return True
            except AttributeError:
                # If SendRawCommand is not available, return False
                return False

        return False

    def set_all(self, color: Tuple[int, int, int]) -> bool:
        """
        Set all LEDs to the same color.

        Args:
            color: (r, g, b) tuple

        Returns:
            True if successful
        """
        colors = [color] * self.num_leds
        return self.update(colors)

    def clear(self) -> bool:
        """
        Turn off all LEDs (set to black).

        Returns:
            True if successful
        """
        return self.set_all((0, 0, 0))

    def force_full_update(self, colors: Union[bytes, bytearray, List[Tuple[int, int, int]]]) -> bool:
        """
        Force a full buffer update without delta compression.

        Useful after connection issues or to reset state.

        Args:
            colors: Either raw bytes (RGB, 3 bytes per LED) or list of (r, g, b) tuples

        Returns:
            True if successful
        """
        # Handle raw bytes input
        if isinstance(colors, (bytes, bytearray)):
            expected_bytes = self.num_leds * 3
            if len(colors) != expected_bytes:
                raise ValueError(
                    f"Expected {expected_bytes} bytes ({self.num_leds} LEDs * 3), got {len(colors)}")
            buffer = bytes(colors)
        else:
            # Handle list of tuples
            if len(colors) != self.num_leds:
                raise ValueError(
                    f"Expected {self.num_leds} colors, got {len(colors)}")

            # Convert to byte array
            buffer = bytearray()
            for r, g, b in colors:
                buffer.append(r & 0xFF)
                buffer.append(g & 0xFF)
                buffer.append(b & 0xFF)
            buffer = bytes(buffer)

        # Force full update
        command_bytes = self._buffer_manager.force_full_update(bytes(buffer))

        if command_bytes and self._cpp_device:
            try:
                self._cpp_device.SendRawCommand(command_bytes)
                return True
            except AttributeError:
                return False

        return False

    def reset(self) -> None:
        """
        Reset the buffer state, forcing the next update to be full.

        Useful after reconnecting or when you suspect the device state
        is out of sync.
        """
        self._buffer_manager.reset()

    @property
    def frame_count(self) -> int:
        """Get the current frame count since last full refresh."""
        return self._buffer_manager.frame_count

    @property
    def full_refresh_interval(self) -> int:
        """Get the full refresh interval."""
        return self._buffer_manager.full_refresh_interval

    @full_refresh_interval.setter
    def full_refresh_interval(self, value: int) -> None:
        """Set the full refresh interval."""
        self._buffer_manager.full_refresh_interval = value
