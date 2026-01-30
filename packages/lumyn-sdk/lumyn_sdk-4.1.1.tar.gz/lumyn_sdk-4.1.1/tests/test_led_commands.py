"""
Tests for LED command buffer serialization.

Verifies that the CommandBuilder produces correct byte layouts matching
what the firmware expects:

    [CommandHeader (2 bytes)][Command Data (variable)]

Where CommandHeader is:
    - type: uint8_t (CommandType enum)
    - ledType/systemType: uint8_t (subtype enum, union in C++)

And Command Data depends on the command type.
"""

from .test_helpers import (
    COMMAND_HEADER_SIZE,
    SET_ANIMATION_DATA_SIZE,
    SET_COLOR_DATA_SIZE,
    SET_ANIMATION_SEQUENCE_DATA_SIZE,
    SET_BITMAP_DATA_SIZE,
    CommandType,
    LEDCommandType,
    parse_command_header,
    parse_set_animation_data,
    parse_set_color_data,
    parse_set_animation_sequence_data,
)
import pytest
import struct
import sys
import os


class TestSetAnimationCommand:
    """Tests for SetAnimation command buffer format."""

    def test_buffer_size(self, command_builder, animation_color_factory):
        """SetAnimation buffer should be exactly CommandHeader + SetAnimationData."""
        color = animation_color_factory(255, 128, 64)
        buffer = command_builder.buildSetAnimation(
            zone_id=0x1234,
            animation_id=0x5678,
            color=color,
            delay=100,
            reversed=False,
            one_shot=False
        )

        expected_size = COMMAND_HEADER_SIZE + SET_ANIMATION_DATA_SIZE
        assert len(buffer) == expected_size, \
            f"Buffer size {len(buffer)} != expected {expected_size}"

    def test_command_header(self, command_builder, animation_color_factory):
        """SetAnimation should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetAnimation(
            zone_id=0,
            animation_id=0,
            color=color
        )

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED, \
            f"CommandType should be LED ({CommandType.LED}), got {header['type']}"
        assert header['subtype'] == LEDCommandType.SET_ANIMATION, \
            f"LEDCommandType should be SetAnimation ({LEDCommandType.SET_ANIMATION}), got {header['subtype']}"

    def test_zone_id_serialization(self, command_builder, animation_color_factory):
        """Zone ID should be serialized as little-endian uint16_t."""
        color = animation_color_factory(0, 0, 0)
        test_zone_id = 0xABCD

        buffer = command_builder.buildSetAnimation(
            zone_id=test_zone_id,
            animation_id=0,
            color=color
        )

        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['zoneId'] == test_zone_id, \
            f"Zone ID {data['zoneId']:#x} != expected {test_zone_id:#x}"

    def test_animation_id_serialization(self, command_builder, animation_color_factory):
        """Animation ID should be serialized as little-endian uint16_t."""
        color = animation_color_factory(0, 0, 0)
        test_animation_id = 0x1234

        buffer = command_builder.buildSetAnimation(
            zone_id=0,
            animation_id=test_animation_id,
            color=color
        )

        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['animationId'] == test_animation_id, \
            f"Animation ID {data['animationId']:#x} != expected {test_animation_id:#x}"

    def test_delay_serialization(self, command_builder, animation_color_factory):
        """Delay should be serialized as little-endian uint16_t."""
        color = animation_color_factory(0, 0, 0)
        test_delay = 500

        buffer = command_builder.buildSetAnimation(
            zone_id=0,
            animation_id=0,
            color=color,
            delay=test_delay
        )

        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['delay'] == test_delay, \
            f"Delay {data['delay']} != expected {test_delay}"

    def test_color_serialization(self, command_builder, animation_color_factory):
        """Color RGB values should be serialized correctly."""
        test_r, test_g, test_b = 255, 128, 64
        color = animation_color_factory(test_r, test_g, test_b)

        buffer = command_builder.buildSetAnimation(
            zone_id=0,
            animation_id=0,
            color=color
        )

        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['color']['r'] == test_r, f"Red {data['color']['r']} != {test_r}"
        assert data['color']['g'] == test_g, f"Green {data['color']['g']} != {test_g}"
        assert data['color']['b'] == test_b, f"Blue {data['color']['b']} != {test_b}"

    def test_reversed_flag(self, command_builder, animation_color_factory):
        """Reversed flag should be serialized in flags byte bit 0."""
        color = animation_color_factory(0, 0, 0)

        # Test reversed = False
        buffer_not_reversed = command_builder.buildSetAnimation(
            zone_id=0, animation_id=0, color=color, reversed=False
        )
        data = parse_set_animation_data(
            buffer_not_reversed, COMMAND_HEADER_SIZE)
        assert data['reversed'] == False, "Reversed should be False"

        # Test reversed = True
        buffer_reversed = command_builder.buildSetAnimation(
            zone_id=0, animation_id=0, color=color, reversed=True
        )
        data = parse_set_animation_data(buffer_reversed, COMMAND_HEADER_SIZE)
        assert data['reversed'] == True, "Reversed should be True"

    def test_one_shot_flag(self, command_builder, animation_color_factory):
        """OneShot flag should be serialized in flags byte bit 1."""
        color = animation_color_factory(0, 0, 0)

        # Test oneShot = False
        buffer_not_oneshot = command_builder.buildSetAnimation(
            zone_id=0, animation_id=0, color=color, one_shot=False
        )
        data = parse_set_animation_data(
            buffer_not_oneshot, COMMAND_HEADER_SIZE)
        assert data['oneShot'] == False, "OneShot should be False"

        # Test oneShot = True
        buffer_oneshot = command_builder.buildSetAnimation(
            zone_id=0, animation_id=0, color=color, one_shot=True
        )
        data = parse_set_animation_data(buffer_oneshot, COMMAND_HEADER_SIZE)
        assert data['oneShot'] == True, "OneShot should be True"

    def test_combined_flags(self, command_builder, animation_color_factory):
        """Both reversed and oneShot flags should work together."""
        color = animation_color_factory(0, 0, 0)

        buffer = command_builder.buildSetAnimation(
            zone_id=0, animation_id=0, color=color,
            reversed=True, one_shot=True
        )
        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['reversed'] == True, "Reversed should be True"
        assert data['oneShot'] == True, "OneShot should be True"

    def test_full_command_layout(self, command_builder, animation_color_factory, id_creator):
        """Test complete command layout with realistic values."""
        # Use IDCreator like the SDK does internally
        zone_hash = id_creator.createId("front_leds")
        animation_hash = id_creator.createId("Breathe")

        color = animation_color_factory(0, 255, 0)  # Green
        delay = 250

        buffer = command_builder.buildSetAnimation(
            zone_id=zone_hash,
            animation_id=animation_hash,
            color=color,
            delay=delay,
            reversed=False,
            one_shot=False
        )

        # Verify header
        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_ANIMATION

        # Verify data
        data = parse_set_animation_data(buffer, COMMAND_HEADER_SIZE)
        assert data['zoneId'] == zone_hash
        assert data['animationId'] == animation_hash
        assert data['delay'] == delay
        assert data['color'] == {'r': 0, 'g': 255, 'b': 0}
        assert data['reversed'] == False
        assert data['oneShot'] == False


class TestSetColorCommand:
    """Tests for SetColor command buffer format."""

    def test_buffer_size(self, command_builder, animation_color_factory):
        """SetColor buffer should be exactly CommandHeader + SetColorData."""
        color = animation_color_factory(255, 0, 0)
        buffer = command_builder.buildSetColor(zone_id=0x1234, color=color)

        expected_size = COMMAND_HEADER_SIZE + SET_COLOR_DATA_SIZE
        assert len(buffer) == expected_size, \
            f"Buffer size {len(buffer)} != expected {expected_size}"

    def test_command_header(self, command_builder, animation_color_factory):
        """SetColor should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetColor(zone_id=0, color=color)

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_COLOR

    def test_zone_id_and_color(self, command_builder, animation_color_factory):
        """SetColor should serialize zone ID and color correctly."""
        test_zone_id = 0x5678
        test_r, test_g, test_b = 255, 100, 50
        color = animation_color_factory(test_r, test_g, test_b)

        buffer = command_builder.buildSetColor(
            zone_id=test_zone_id, color=color)
        data = parse_set_color_data(buffer, COMMAND_HEADER_SIZE)

        assert data['zoneId'] == test_zone_id
        assert data['color']['r'] == test_r
        assert data['color']['g'] == test_g
        assert data['color']['b'] == test_b


class TestSetAnimationSequenceCommand:
    """Tests for SetAnimationSequence command buffer format."""

    def test_buffer_size(self, command_builder):
        """SetAnimationSequence buffer should be correct size."""
        buffer = command_builder.buildSetAnimationSequence(
            zone_id=0, sequence_id=0)

        expected_size = COMMAND_HEADER_SIZE + SET_ANIMATION_SEQUENCE_DATA_SIZE
        assert len(buffer) == expected_size

    def test_command_header(self, command_builder):
        """SetAnimationSequence should have correct CommandHeader."""
        buffer = command_builder.buildSetAnimationSequence(
            zone_id=0, sequence_id=0)

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_ANIMATION_SEQUENCE

    def test_zone_and_sequence_ids(self, command_builder, id_creator):
        """SetAnimationSequence should serialize IDs correctly."""
        zone_hash = id_creator.createId("left_strip")
        seq_hash = id_creator.createId("rainbow_cycle")

        buffer = command_builder.buildSetAnimationSequence(
            zone_id=zone_hash,
            sequence_id=seq_hash
        )
        data = parse_set_animation_sequence_data(buffer, COMMAND_HEADER_SIZE)

        assert data['zoneId'] == zone_hash
        assert data['sequenceId'] == seq_hash


class TestSetAnimationGroupCommand:
    """Tests for SetAnimationGroup command buffer format."""

    def test_command_header(self, command_builder, animation_color_factory):
        """SetAnimationGroup should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetAnimationGroup(
            group_id=0, animation_id=0, color=color
        )

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_ANIMATION_GROUP


class TestSetColorGroupCommand:
    """Tests for SetColorGroup command buffer format."""

    def test_command_header(self, command_builder, animation_color_factory):
        """SetColorGroup should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetColorGroup(group_id=0, color=color)

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_COLOR_GROUP


class TestBitmapCommands:
    """Tests for SetBitmap and SetBitmapGroup commands."""

    def test_set_bitmap_header(self, command_builder, animation_color_factory):
        """SetBitmap should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetBitmap(
            zone_id=0, bitmap_id=0, color=color
        )

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_BITMAP

    def test_set_bitmap_group_header(self, command_builder, animation_color_factory):
        """SetBitmapGroup should have correct CommandHeader."""
        color = animation_color_factory(0, 0, 0)
        buffer = command_builder.buildSetBitmapGroup(
            group_id=0, bitmap_id=0, color=color
        )

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.LED
        assert header['subtype'] == LEDCommandType.SET_BITMAP_GROUP


class TestAnimationBuilder:
    """Tests for AnimationBuilder fluent API."""

    def test_builder_creation(self, mock_led_handler):
        """AnimationBuilder should be created from set_animation with Animation enum."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Chase)
        assert builder is not None
        assert hasattr(builder, 'for_zone')
        assert hasattr(builder, 'with_color')
        assert hasattr(builder, 'execute')

    def test_default_values(self, mock_led_handler):
        """AnimationBuilder should use common-sourced defaults when available."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Chase)
        # Defaults should be populated (values come from common via bindings when available).
        assert builder._color is not None
        assert builder._delay_ms is not None
        assert isinstance(builder._delay_ms, int)
        assert builder._delay_ms >= 0

    def test_for_zone(self, mock_led_handler):
        """AnimationBuilder.for_zone() should set zone and clear group."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_zone("front")
        assert builder._zone_id == "front"
        assert builder._group_id is None

    def test_for_group(self, mock_led_handler):
        """AnimationBuilder.for_group() should set group and clear zone."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_group("all_leds")
        assert builder._group_id == "all_leds"
        assert builder._zone_id is None

    def test_with_color(self, mock_led_handler):
        """AnimationBuilder.with_color() should update color."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.with_color((255, 0, 0))
        assert builder._color == (255, 0, 0)

    def test_with_delay(self, mock_led_handler):
        """AnimationBuilder.with_delay() should update delay."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.with_delay(100)
        assert builder._delay_ms == 100

    def test_reverse(self, mock_led_handler):
        """AnimationBuilder.reverse() should update reversed flag."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.reverse(True)
        assert builder._reversed is True

    def test_method_chaining(self, mock_led_handler):
        """AnimationBuilder should support method chaining."""
        from lumyn_sdk.enums import Animation
        builder = (mock_led_handler.set_animation(Animation.Chase)
                   .for_zone("front")
                   .with_color((255, 0, 0))
                   .with_delay(40)
                   .reverse(False))
        assert builder._zone_id == "front"
        assert builder._color == (255, 0, 0)
        assert builder._delay_ms == 40
        assert builder._reversed is False

    def test_execute_requires_zone_or_group(self, mock_led_handler):
        """AnimationBuilder.execute() should raise error if zone/group not set."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        with pytest.raises(RuntimeError, match="Must call.*ForZone.*ForGroup"):
            builder.execute()

    def test_execute_calls_handler(self, mock_led_handler):
        """AnimationBuilder.execute() should execute the animation."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_zone("front")
        assert builder._executed is False
        builder.execute()
        assert builder._executed is True

    def test_run_once_executes(self, mock_led_handler):
        """AnimationBuilder.run_once() should execute and set one_shot."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_zone("front")
        builder.run_once(True)
        assert builder._one_shot is True
        assert builder._executed is True

    def test_cannot_reuse_after_execution(self, mock_led_handler):
        """AnimationBuilder should raise error if used after execution."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_zone("front")
        builder.execute()
        with pytest.raises(RuntimeError, match="already been executed"):
            builder.for_zone("back")

    def test_group_execution(self, mock_led_handler):
        """AnimationBuilder should execute for groups."""
        from lumyn_sdk.enums import Animation
        builder = mock_led_handler.set_animation(Animation.Breathe)
        builder.for_group("all_leds")
        assert builder._group_id == "all_leds"
        assert builder._zone_id is None
        builder.execute()
        assert builder._executed is True


class TestMatrixTextBuilder:
    """Tests for MatrixTextBuilder fluent API."""

    def test_builder_creation(self, mock_led_handler):
        """MatrixTextBuilder should be created from set_text."""
        builder = mock_led_handler.set_text("HELLO")
        assert builder is not None
        assert hasattr(builder, 'for_zone')
        assert hasattr(builder, 'with_color')
        assert hasattr(builder, 'execute')

    def test_default_values(self, mock_led_handler):
        """MatrixTextBuilder should have sensible defaults."""
        builder = mock_led_handler.set_text("HELLO")
        assert builder._color == (255, 255, 255)  # White
        assert builder._delay_ms == 50
        # Direction enum - compare by value since name casing may differ
        from lumyn_sdk._bindings.connectorx import MatrixTextScrollDirection as CppDirection
        assert builder._direction.value == CppDirection.LEFT.value or builder._direction == CppDirection.LEFT
        assert builder._one_shot is False

    def test_for_zone(self, mock_led_handler):
        """MatrixTextBuilder.for_zone() should set zone."""
        builder = mock_led_handler.set_text("HELLO")
        builder.for_zone("front-matrix")
        assert builder._zone_id == "front-matrix"
        assert builder._group_id is None

    def test_with_color(self, mock_led_handler):
        """MatrixTextBuilder.with_color() should update color."""
        builder = mock_led_handler.set_text("HELLO")
        builder.with_color((255, 0, 0))
        assert builder._color == (255, 0, 0)

    def test_with_delay(self, mock_led_handler):
        """MatrixTextBuilder.with_delay() should update delay."""
        builder = mock_led_handler.set_text("HELLO")
        builder.with_delay(100)
        assert builder._delay_ms == 100

    def test_with_direction(self, mock_led_handler):
        """MatrixTextBuilder.with_direction() should update direction."""
        from lumyn_sdk._bindings.connectorx import MatrixTextScrollDirection as CppDirection
        builder = mock_led_handler.set_text("HELLO")
        builder.with_direction(CppDirection.RIGHT)
        assert builder._direction == CppDirection.RIGHT

    def test_method_chaining(self, mock_led_handler):
        """MatrixTextBuilder should support method chaining."""
        from lumyn_sdk._bindings.connectorx import MatrixTextScrollDirection as CppDirection
        builder = (mock_led_handler.set_text("HELLO")
                   .for_zone("front-matrix")
                   .with_color((255, 0, 0))
                   .with_delay(50)
                   .with_direction(CppDirection.LEFT))
        assert builder._zone_id == "front-matrix"
        assert builder._color == (255, 0, 0)
        assert builder._delay_ms == 50

    def test_execute_requires_zone_or_group(self, mock_led_handler):
        """MatrixTextBuilder.execute() should raise error if zone/group not set."""
        builder = mock_led_handler.set_text("HELLO")
        with pytest.raises(RuntimeError, match="Must call.*ForZone.*ForGroup"):
            builder.execute()

    def test_execute_calls_handler(self, mock_led_handler):
        """MatrixTextBuilder.execute() should execute the text."""
        builder = mock_led_handler.set_text("HELLO")
        builder.for_zone("front-matrix")
        assert builder._executed is False
        builder.execute()
        assert builder._executed is True

    def test_group_execution(self, mock_led_handler):
        """MatrixTextBuilder should execute for groups."""
        builder = mock_led_handler.set_text("HELLO")
        builder.for_group("all_matrices")
        assert builder._group_id == "all_matrices"
        assert builder._zone_id is None
        builder.execute()
        assert builder._executed is True


class TestImageSequenceBuilder:
    """Tests for ImageSequenceBuilder fluent API."""

    def test_builder_creation(self, mock_led_handler):
        """ImageSequenceBuilder should be created from set_image_sequence."""
        builder = mock_led_handler.set_image_sequence("Emoji_16x16_unknown")
        assert builder is not None
        assert hasattr(builder, 'for_zone')
        assert hasattr(builder, 'with_color')
        assert hasattr(builder, 'execute')

    def test_default_values(self, mock_led_handler):
        """ImageSequenceBuilder should have sensible defaults."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        assert builder._color == (255, 255, 255)  # White
        assert builder._set_color is True
        assert builder._one_shot is False

    def test_for_zone(self, mock_led_handler):
        """ImageSequenceBuilder.for_zone() should set zone."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        builder.for_zone("front-matrix")
        assert builder._zone_id == "front-matrix"
        assert builder._group_id is None

    def test_with_color(self, mock_led_handler):
        """ImageSequenceBuilder.with_color() should update color."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        builder.with_color((120, 0, 100))
        assert builder._color == (120, 0, 100)

    def test_set_color(self, mock_led_handler):
        """ImageSequenceBuilder.set_color() should update set_color flag."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        builder.set_color(False)
        assert builder._set_color is False

    def test_method_chaining(self, mock_led_handler):
        """ImageSequenceBuilder should support method chaining."""
        builder = (mock_led_handler.set_image_sequence("test_sequence")
                   .for_zone("front-matrix")
                   .with_color((120, 0, 100))
                   .set_color(True))
        assert builder._zone_id == "front-matrix"
        assert builder._color == (120, 0, 100)
        assert builder._set_color is True

    def test_execute_requires_zone_or_group(self, mock_led_handler):
        """ImageSequenceBuilder.execute() should raise error if zone/group not set."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        with pytest.raises(RuntimeError, match="Must call.*ForZone.*ForGroup"):
            builder.execute()

    def test_execute_calls_handler(self, mock_led_handler):
        """ImageSequenceBuilder.execute() should execute the sequence."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        builder.for_zone("front-matrix")
        assert builder._executed is False
        builder.execute()
        assert builder._executed is True

    def test_group_execution(self, mock_led_handler):
        """ImageSequenceBuilder should execute for groups."""
        builder = mock_led_handler.set_image_sequence("test_sequence")
        builder.for_group("all_matrices")
        assert builder._group_id == "all_matrices"
        assert builder._zone_id is None
        builder.execute()
        assert builder._executed is True
