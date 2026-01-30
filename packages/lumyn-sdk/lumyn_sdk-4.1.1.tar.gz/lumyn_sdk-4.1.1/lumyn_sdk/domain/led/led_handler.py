"""
LedHandler - LED control interface using C++ SDK builders.

Provides Python-friendly methods for controlling LEDs through the C++ SDK builder pattern.
"""

from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lumyn_sdk._bindings.connectorx import AnimationBuilder, ImageSequenceBuilder, MatrixTextBuilder


class IllegalStateError(Exception):
    """Raised when an operation is performed in an illegal state (e.g., using a builder after execution)."""
    pass


class LedHandler:
    """
    Handler for LED control operations.

    Wraps C++ SDK LED methods to provide a clean Python API using the builder pattern.
    """

    def __init__(self, cpp_device):
        """
        Initialize LED handler.

        Args:
            cpp_device: The C++ SDK ConnectorXInternal instance
        """
        self._cpp_device = cpp_device

    def set_color(self, zone_id: str, color: Tuple[int, int, int]) -> None:
        """
        Set a solid color on a zone.

        Args:
            zone_id: Zone identifier (e.g., "zone_0", "front_left")
            color: RGB tuple (0-255 each)
        """
        if self._cpp_device:
            # Convert Python tuple to C++ Color format
            # C++ SDK expects: SetColor(zone_id, color)
            # where color is (r, g, b) tuple
            self._cpp_device.SetColor(zone_id, color)

    def set_group_color(self, group_id: str, color: Tuple[int, int, int]) -> None:
        """
        Set a solid color on a group.

        Args:
            group_id: Group identifier (e.g., "all_leds", "front_leds")
            color: RGB tuple (0-255 each)
        """
        if self._cpp_device:
            self._cpp_device.SetGroupColor(group_id, color)

    def create_direct_led(self, zone_id: str, num_leds: int, full_refresh_interval: int = 100):
        """
        Create a DirectLED instance for low-level LED control.

        Args:
            zone_id: Zone identifier (e.g., "zone_0", "front_leds")
            num_leds: Number of LEDs in the zone
            full_refresh_interval: How often to force full refresh (default: 100 frames)

        Returns:
            DirectLED instance for efficient pixel-level control
        """
        from .direct_led import DirectLED
        return DirectLED(self._cpp_device, zone_id, num_leds, full_refresh_interval)

    def set_animation(self, animation_or_zone, animation=None, color: Optional[Tuple[int, int, int]] = None,
                      delay_ms: int = 100, reversed: bool = False, one_shot: bool = False):
        """
        Set an animation - supports both builder pattern and direct calls.

        Builder pattern (preferred):
            led.set_animation(Animation.Chase).for_zone("zone_0").with_color((255,0,0)).execute()

        Direct call:
            led.set_animation("zone_0", Animation.Chase, (255, 0, 0))

        Args:
            animation_or_zone: Animation enum (builder) or zone_id (direct)
            animation: Animation enum when using direct call
            color: Optional RGB color tuple
            delay_ms: Animation delay in milliseconds (default: 100)
            reversed: Play animation in reverse (default: False)
            one_shot: Play once then stop (default: False)

        Returns:
            AnimationBuilder for fluent API or None for direct call
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")

        # Check if using builder pattern (first arg is Animation enum)
        from ..._bindings.connectorx import Animation as CppAnimation
        from ...enums import Animation as PyAnimation

        if animation is None and (isinstance(animation_or_zone, (CppAnimation, PyAnimation)) or
                                  (hasattr(animation_or_zone, '__class__') and
                                  animation_or_zone.__class__.__name__ == 'Animation')):
            # Builder pattern: set_animation(Animation.Chase)
            # Convert Python enum to C++ enum if needed
            cpp_animation = CppAnimation(int(animation_or_zone)) if isinstance(
                animation_or_zone, PyAnimation) else animation_or_zone
            return self._cpp_device.SetAnimation(cpp_animation)

        # Direct pattern: set_animation("zone_id", Animation.Chase, ...)
        zone_id = animation_or_zone
        cpp_animation = CppAnimation(int(animation)) if isinstance(
            animation, PyAnimation) else animation
        builder = self._cpp_device.SetAnimation(cpp_animation).ForZone(zone_id)

        if color is not None:
            builder = builder.WithColor(color)
        if delay_ms != 100:
            builder = builder.WithDelay(delay_ms)
        if reversed:
            builder = builder.Reverse(True)

        if one_shot:
            builder.RunOnce()
        else:
            builder.execute()

        return builder

    def set_group_animation(self, group_id: str, animation, color: Optional[Tuple[int, int, int]] = None,
                            delay_ms: int = 100, reversed: bool = False, one_shot: bool = False) -> 'AnimationBuilder':
        """
        Set an animation on a group using the builder pattern.

        Args:
            group_id: Group identifier
            animation: Animation enum value
            color: Optional RGB color tuple (default: animation default)
            delay_ms: Animation delay in milliseconds (default: 100)
            reversed: Play animation in reverse (default: False)
            one_shot: Play once then stop (default: False)

        Returns:
            AnimationBuilder for fluent API usage

        Example:
            led.set_group_animation("all_leds", Animation.Breathe, (0, 0, 255))
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")

        builder = self._cpp_device.SetAnimation(animation).ForGroup(group_id)

        if color is not None:
            builder = builder.WithColor(color)
        if delay_ms != 100:
            builder = builder.WithDelay(delay_ms)
        if reversed:
            builder = builder.Reverse(True)

        if one_shot:
            builder.RunOnce()
        else:
            builder.execute()

        return builder

    def set_image_sequence(self, sequence_or_zone, sequence_id=None, color: Optional[Tuple[int, int, int]] = None,
                           set_color: bool = False, one_shot: bool = False):
        """
        Set an image sequence - supports both builder pattern and direct calls.

        Builder pattern (preferred):
            led.set_image_sequence("seq_id").for_zone("zone_0").with_color((255,0,0)).execute()

        Direct call:
            led.set_image_sequence("zone_0", "seq_id", (255, 0, 0))

        Args:
            sequence_or_zone: Sequence ID (builder) or zone_id (direct)
            sequence_id: Sequence ID when using direct call
            color: Optional RGB color tuple
            set_color: Whether to override sequence colors
            one_shot: Play once then stop (default: False)

        Returns:
            ImageSequenceBuilder for fluent API or None for direct call
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")

        # Check if using builder pattern
        if sequence_id is None:
            # Builder pattern: set_image_sequence("sequence_id")
            return self._cpp_device.SetImageSequence(sequence_or_zone)

        # Direct pattern: set_image_sequence("zone_id", "sequence_id", ...)
        zone_id = sequence_or_zone
        builder = self._cpp_device.SetImageSequence(
            sequence_id).ForZone(zone_id)

        if color is not None and set_color:
            builder = builder.WithColor(color)

        if one_shot:
            builder.RunOnce()
        else:
            builder.execute()

        return builder

    def set_animation_sequence(self, zone_id: str, sequence_id: str):
        """
        Play a predefined animation sequence on a zone.

        Animation sequences are series of animations defined in the device
        configuration JSON (e.g., breathe -> chase -> sparkle).

        Args:
            zone_id: Zone identifier
            sequence_id: Sequence identifier from configuration file

        Note:
            Animation sequences must be defined in the device configuration JSON.
            This is different from image sequences which display bitmaps.
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")
        self._cpp_device.SetAnimationSequence(zone_id, sequence_id)

    def set_group_animation_sequence(self, group_id: str, sequence_id: str):
        """
        Play a predefined animation sequence on a group.

        Args:
            group_id: Group identifier
            sequence_id: Sequence identifier from configuration file
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")
        self._cpp_device.SetGroupAnimationSequence(group_id, sequence_id)

    def set_text(self, text_or_zone, text=None, color: Optional[Tuple[int, int, int]] = None,
                 delay_ms: int = 50, scroll_direction=None):
        """
        Display text on a matrix zone - supports both builder pattern and direct calls.

        Builder pattern (preferred):
            led.set_text("Hello").for_zone("matrix").with_color((255,0,0)).execute()

        Direct call:
            led.set_text("matrix", "Hello", (255, 0, 0))

        Args:
            text_or_zone: Text string (builder) or zone_id (direct)
            text: Text when using direct call
            color: Optional RGB color tuple
            delay_ms: Scroll delay in milliseconds (default: 50)
            scroll_direction: Optional scroll direction

        Returns:
            MatrixTextBuilder for fluent API or None for direct call
        """
        if not self._cpp_device:
            raise RuntimeError("Device not connected")

        # Check if using builder pattern (text is None means first arg is the text)
        if text is None:
            # Builder pattern: set_text("Hello")
            return self._cpp_device.SetText(text_or_zone)

        # Direct pattern: set_text("zone_id", "Hello", ...)
        zone_id = text_or_zone
        builder = self._cpp_device.SetText(text).ForZone(zone_id)

        if color is not None:
            builder = builder.WithColor(color)
        if delay_ms != 50:
            builder = builder.WithDelay(delay_ms)
        if scroll_direction is not None:
            builder = builder.WithDirection(scroll_direction)

        builder.execute()

        return builder
