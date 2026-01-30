"""
Type stubs for lumyn_sdk.domain.led.led_handler

NOTE: Animation and MatrixTextScrollDirection are imported from enums.py here
for type stub purposes, but at runtime the C++ bound versions from
_bindings.Animation and command.MatrixTextScrollDirection are preferred.
"""

from typing import Any, Callable, Optional, Tuple, Union
from ...enums import Animation, MatrixTextScrollDirection, MatrixTextFont, MatrixTextAlign

Color = Union[Tuple[int, int, int], Tuple[float, float, float]]


class MatrixTextBuilder:
    """Builder for setting matrix text with a fluent API."""
    def __init__(self, handler: 'LedHandler', text: str) -> None: ...
    def for_zone(self, zone_id: str) -> 'MatrixTextBuilder': ...
    def for_group(self, group_id: str) -> 'MatrixTextBuilder': ...
    def with_color(self, color: Color) -> 'MatrixTextBuilder': ...
    def with_delay(self, delay_ms: int) -> 'MatrixTextBuilder': ...
    def with_direction(self, direction: MatrixTextScrollDirection) -> 'MatrixTextBuilder': ...
    def with_background_color(self, color: Color) -> 'MatrixTextBuilder': ...
    def with_font(self, font: MatrixTextFont) -> 'MatrixTextBuilder': ...
    def with_align(self, align: MatrixTextAlign) -> 'MatrixTextBuilder': ...
    def smooth_scroll(self, enabled: bool) -> 'MatrixTextBuilder': ...
    def show_background(self, enabled: bool) -> 'MatrixTextBuilder': ...
    def ping_pong(self, enabled: bool) -> 'MatrixTextBuilder': ...
    def no_scroll(self, enabled: bool) -> 'MatrixTextBuilder': ...
    def with_y_offset(self, y_offset: int) -> 'MatrixTextBuilder': ...
    def run_once(self, one_shot: bool) -> 'MatrixTextBuilder': ...
    def execute(self) -> None: ...


class DirectLED:
    """Manages direct LED buffer updates with automatic delta compression.

    This class wraps the C++ DirectBufferManager to provide efficient
    delta-compressed LED updates. Requires specifying the buffer length
    upfront for validation.

    Usage:
        led_handler = LedHandler(command_handler)
        direct_led = led_handler.create_direct_led("FrontLEDs", num_leds=50)
        direct_led.update(rgb_buffer)  # Automatically handles delta compression
    """

    BYTES_PER_LED: int  # = 3 (RGB)
    zone_id: str
    num_leds: int

    def __init__(
        self,
        zone_id: str,
        num_leds: int,
        command_handler,
        full_refresh_interval: int = 100
    ) -> None:
        """Initialize DirectLED for a zone.

        Args:
            zone_id: LED zone identifier
            num_leds: Number of LEDs in the zone
            command_handler: Command handler for sending commands
            full_refresh_interval: Send full buffer every N frames (default: 100, 0 to disable)
        """
        ...

    @property
    def buffer_length(self) -> int:
        """Get the expected buffer length in bytes (num_leds * BYTES_PER_LED)."""
        ...

    def update(self, buffer: bytes) -> None:
        """Update LED buffer, automatically using delta compression when beneficial.

        Args:
            buffer: Raw RGB bytes (BYTES_PER_LED bytes per LED)

        Raises:
            ValueError: If buffer length doesn't match expected length
        """
        ...

    def force_full_update(self, buffer: bytes) -> None:
        """Force a full buffer update (no delta compression).

        Args:
            buffer: Raw RGB/RGBW bytes

        Raises:
            ValueError: If buffer length doesn't match expected length
        """
        ...

    def reset(self) -> None:
        """Reset state, forcing next update to be a full buffer."""
        ...

    @property
    def full_refresh_interval(self) -> int:
        """Get the full refresh interval."""
        ...

    @full_refresh_interval.setter
    def full_refresh_interval(self, value: int) -> None:
        """Set the full refresh interval."""
        ...

    @property
    def frame_count(self) -> int:
        """Get current frame count since last full refresh."""
        ...


class LedHandler:
    """Handler for LED operations and animations"""

    def __init__(
        self, connector_instance: Optional[Callable[[Any], None]]) -> None: ...

    def create_direct_led(
        self,
        zone_id: str,
        num_leds: int,
        full_refresh_interval: int = 100
    ) -> DirectLED:
        """Create a DirectLED instance for efficient buffer updates.

        Args:
            zone_id: LED zone identifier
            num_leds: Number of LEDs in the zone
            full_refresh_interval: Send full buffer every N frames (default: 100, 0 to disable)

        Returns:
            DirectLED instance for the zone
        """
        ...

    def create_buffer_manager(
        self,
        zone_id: str,
        num_leds: int = 0,
        full_refresh_interval: int = 100
    ) -> DirectLED:
        """Create a stateful buffer manager for a zone.

        DEPRECATED: Use create_direct_led() instead.

        Args:
            zone_id: LED zone identifier
            num_leds: Number of LEDs (required for new API)
            full_refresh_interval: Send full buffer every N frames (default: 100)

        Returns:
            DirectLED instance for the zone
        """
        ...

    def set_color(self, zone_id: str, color: Color) -> None: ...
    def set_group_color(self, group_id: str, color: Color) -> None: ...

    def set_animation(
        self,
        zone_id: str,
        animation: Animation,
        color: Color,
        delay_ms: int = 250,
        reversed: bool = False,
        one_shot: bool = False
    ) -> None: ...

    def set_group_animation(
        self,
        group_id: str,
        animation: Animation,
        color: Color,
        delay_ms: int = 250,
        reversed: bool = False,
        one_shot: bool = False
    ) -> None: ...

    def set_animation_sequence(
        self, zone_id: str, sequence_id: str) -> None: ...

    def set_group_animation_sequence(
        self, group_id: str, sequence_id: str) -> None: ...

    def set_image_sequence(
        self,
        zone_id: str,
        sequence_id: str,
        color: Color,
        set_color: bool = False,
        one_shot: bool = False
    ) -> None: ...

    def set_text(self, text: str) -> MatrixTextBuilder: ...

    def set_group_image_sequence(
        self,
        group_id: str,
        sequence_id: str,
        color: Color,
        set_color: bool = False,
        one_shot: bool = False
    ) -> None: ...

    def set_matrix_text(
        self,
        zone_id: str,
        text: str,
        color: Color,
        direction: MatrixTextScrollDirection = MatrixTextScrollDirection.LEFT,
        delay_ms: int = 500,
        one_shot: bool = False,
        bg_color: Color = (0, 0, 0),
        font: MatrixTextFont = MatrixTextFont.BUILTIN,
        align: MatrixTextAlign = MatrixTextAlign.LEFT,
        smooth_scroll: bool = False,
        show_background: bool = False,
        ping_pong: bool = False,
        no_scroll: bool = False,
        y_offset: int = 0
    ) -> None: ...

    def set_group_matrix_text(
        self,
        group_id: str,
        text: str,
        color: Color,
        direction: MatrixTextScrollDirection = MatrixTextScrollDirection.LEFT,
        delay_ms: int = 500,
        one_shot: bool = False,
        bg_color: Color = (0, 0, 0),
        font: MatrixTextFont = MatrixTextFont.BUILTIN,
        align: MatrixTextAlign = MatrixTextAlign.LEFT,
        smooth_scroll: bool = False,
        show_background: bool = False,
        ping_pong: bool = False,
        no_scroll: bool = False,
        y_offset: int = 0
    ) -> None: ...

    def set_rgb(self, r: int, g: int, b: int) -> None: ...
    def clear_all(self) -> None: ...
    def start_animation(self, animation: Animation) -> None: ...
    def stop_animation(self) -> None: ...
    def set_zone_color(self, zone_id: str, r: int, g: int, b: int) -> None: ...

    def set_brightness(self, brightness: float) -> None: ...
    def get_brightness(self) -> float: ...
