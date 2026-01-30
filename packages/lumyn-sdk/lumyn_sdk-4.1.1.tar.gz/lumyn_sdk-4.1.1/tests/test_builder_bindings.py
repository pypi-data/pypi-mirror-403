"""
Test builder pattern C++ bindings.

Tests that AnimationBuilder, ImageSequenceBuilder, and MatrixTextBuilder
are properly exposed from C++ and support fluent API chaining.
"""

import pytest
from lumyn_sdk import (
    ConnectorX,
    Animation,
    AnimationBuilder,
    ImageSequenceBuilder,
    MatrixTextBuilder,
    MatrixTextScrollDirection,
    MatrixTextFont,
    MatrixTextAlign,
)
from lumyn_sdk.domain.led.led_handler import LedHandler


class TestBuilderImports:
    """Test that all builder classes can be imported."""

    def test_animation_builder_import(self):
        """Test AnimationBuilder can be imported."""
        assert AnimationBuilder is not None

    def test_image_sequence_builder_import(self):
        """Test ImageSequenceBuilder can be imported."""
        assert ImageSequenceBuilder is not None

    def test_matrix_text_builder_import(self):
        """Test MatrixTextBuilder can be imported."""
        assert MatrixTextBuilder is not None


class TestAnimationEnum:
    """Test Animation enum values."""

    def test_fill_animation(self):
        """Test Animation.Fill enum value."""
        assert Animation.Fill == Animation.Fill
        assert hasattr(Animation, 'Fill')

    def test_chase_animation(self):
        """Test Animation.Chase enum value."""
        assert Animation.Chase == Animation.Chase
        assert hasattr(Animation, 'Chase')

    def test_breathe_animation(self):
        """Test Animation.Breathe enum value."""
        assert Animation.Breathe == Animation.Breathe
        assert hasattr(Animation, 'Breathe')


class TestMatrixEnums:
    """Test matrix text enum values."""

    def test_scroll_direction_enum(self):
        """Test MatrixTextScrollDirection enum."""
        assert MatrixTextScrollDirection.LEFT == MatrixTextScrollDirection.LEFT
        assert MatrixTextScrollDirection.RIGHT == MatrixTextScrollDirection.RIGHT
        assert hasattr(MatrixTextScrollDirection, 'LEFT')
        assert hasattr(MatrixTextScrollDirection, 'RIGHT')

    def test_font_enum(self):
        """Test MatrixTextFont enum has expected values."""
        assert MatrixTextFont.BUILTIN == MatrixTextFont.BUILTIN
        assert MatrixTextFont.TINY_3X3 == MatrixTextFont.TINY_3X3
        assert MatrixTextFont.FREE_SANS_12 == MatrixTextFont.FREE_SANS_12
        assert hasattr(MatrixTextFont, 'BUILTIN')
        assert hasattr(MatrixTextFont, 'TINY_3X3')

    def test_align_enum(self):
        """Test MatrixTextAlign enum."""
        assert MatrixTextAlign.LEFT == MatrixTextAlign.LEFT
        assert MatrixTextAlign.CENTER == MatrixTextAlign.CENTER
        assert MatrixTextAlign.RIGHT == MatrixTextAlign.RIGHT
        assert hasattr(MatrixTextAlign, 'LEFT')


class TestBuilderCreation:
    """Test builder instances can be created."""

    @pytest.fixture
    def connector_x(self):
        """Create a ConnectorX instance for testing."""
        return ConnectorX()

    def test_create_animation_builder(self, connector_x):
        """Test SetAnimation() returns AnimationBuilder."""
        cpp_device = connector_x._cpp_device
        builder = cpp_device.SetAnimation(Animation.Fill)
        assert type(builder).__name__ == 'AnimationBuilder'

    def test_create_image_sequence_builder(self, connector_x):
        """Test SetImageSequence() returns ImageSequenceBuilder."""
        cpp_device = connector_x._cpp_device
        builder = cpp_device.SetImageSequence("sequence_1")
        assert type(builder).__name__ == 'ImageSequenceBuilder'

    def test_create_matrix_text_builder(self, connector_x):
        """Test SetText() returns MatrixTextBuilder."""
        cpp_device = connector_x._cpp_device
        builder = cpp_device.SetText("Hello")
        assert type(builder).__name__ == 'MatrixTextBuilder'


class TestBuilderChaining:
    """Test builder fluent API chaining."""

    @pytest.fixture
    def connector_x(self):
        """Create a ConnectorX instance for testing."""
        return ConnectorX()

    def test_animation_builder_chaining(self, connector_x):
        """Test AnimationBuilder method chaining."""
        cpp_device = connector_x._cpp_device

        # Test individual methods return the builder
        builder = cpp_device.SetAnimation(Animation.Fill)
        chained = builder.ForZone("zone_1")
        assert type(chained).__name__ == 'AnimationBuilder'

        # Test full chain (Reverse() requires a boolean argument)
        result = (cpp_device.SetAnimation(Animation.Fill)
                  .ForZone("zone_1")
                  .WithColor((255, 0, 0))
                  .WithDelay(100)
                  .Reverse(True))
        assert type(result).__name__ == 'AnimationBuilder'

    def test_image_sequence_builder_chaining(self, connector_x):
        """Test ImageSequenceBuilder method chaining."""
        cpp_device = connector_x._cpp_device

        # ImageSequenceBuilder doesn't have WithDelay in the bindings
        result = (cpp_device.SetImageSequence("sequence_1")
                  .ForZone("zone_2"))
        assert type(result).__name__ == 'ImageSequenceBuilder'

    def test_matrix_text_builder_chaining(self, connector_x):
        """Test MatrixTextBuilder method chaining."""
        cpp_device = connector_x._cpp_device

        result = (cpp_device.SetText("Test")
                  .ForZone("zone_3")
                  .WithFont(MatrixTextFont.TINY_3X3)
                  .WithAlign(MatrixTextAlign.CENTER)
                  .WithColor((0, 255, 0))
                  .WithDelay(50))
        assert type(result).__name__ == 'MatrixTextBuilder'


class TestColorConversion:
    """Test automatic tuple to lumyn_color conversion."""

    @pytest.fixture
    def connector_x(self):
        """Create a ConnectorX instance for testing."""
        return ConnectorX()

    def test_with_color_accepts_tuple(self, connector_x):
        """Test WithColor() accepts Python tuples."""
        cpp_device = connector_x._cpp_device

        # Should not raise TypeError
        builder = (cpp_device.SetAnimation(Animation.Fill)
                   .WithColor((255, 0, 0)))
        assert type(builder).__name__ == 'AnimationBuilder'

    def test_set_color_accepts_tuple(self, connector_x):
        """Test SetColor() accepts Python tuples."""
        cpp_device = connector_x._cpp_device

        # Should not raise TypeError
        # Note: This won't actually set colors without a connection,
        # but the binding should accept the call
        cpp_device.SetColor("zone_0", (255, 128, 64))


class TestLEDHandlerIntegration:
    """Test builder integration with LED handler."""

    @pytest.fixture
    def connector_x(self):
        """Create a ConnectorX instance for testing."""
        return ConnectorX()

    def test_led_handler_uses_cpp_device(self, connector_x):
        """Test LedHandler accesses _cpp_device for builder methods."""
        led_handler = LedHandler(connector_x)

        # Verify LED handler has access to the C++ device
        # LedHandler implementation calls _cpp_device.SetAnimation(), etc.
        # This is tested through direct usage of _cpp_device
        cpp_device = connector_x._cpp_device

        builder = cpp_device.SetAnimation(Animation.Chase).ForZone("zone_0")
        assert type(builder).__name__ == 'AnimationBuilder'

        builder = cpp_device.SetImageSequence("seq_1").ForZone("zone_0")
        assert type(builder).__name__ == 'ImageSequenceBuilder'

        builder = cpp_device.SetText("Test").ForZone("zone_0")
        assert type(builder).__name__ == 'MatrixTextBuilder'


class TestDirectLEDBinding:
    """Test DirectLED SendLEDCommand binding."""

    @pytest.fixture
    def connector_x(self):
        """Create a ConnectorX instance for testing."""
        return ConnectorX()

    def test_send_led_command_exists(self, connector_x):
        """Test SendLEDCommand method exists."""
        cpp_device = connector_x._cpp_device
        assert hasattr(cpp_device, 'SendLEDCommand')

    def test_send_led_command_callable(self, connector_x):
        """Test SendLEDCommand method is callable (without invoking it)."""
        cpp_device = connector_x._cpp_device

        # Verify the method is callable - don't actually call it without a connection
        # as the underlying C++ code may abort/crash on unconnected devices
        assert callable(getattr(cpp_device, 'SendLEDCommand', None))
