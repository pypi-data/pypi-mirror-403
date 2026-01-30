"""
Tests for Animation enum and animation-related functionality.

Verifies that all 27 animations are accessible and correctly mapped.
"""

import pytest


# All 27 animations that should be available
EXPECTED_ANIMATIONS = [
    ("None_", 0),      # Note: Python uses None_ to avoid keyword conflict
    ("Fill", 1),
    ("Blink", 2),
    ("Breathe", 3),
    ("RainbowRoll", 4),
    ("SineRoll", 5),
    ("Chase", 6),
    ("FadeIn", 7),
    ("FadeOut", 8),
    ("RainbowCycle", 9),
    ("AlternateBreathe", 10),
    ("GrowingBreathe", 11),
    ("Comet", 12),
    ("Sparkle", 13),
    ("Fire", 14),
    ("Scanner", 15),
    ("TheaterChase", 16),
    ("Twinkle", 17),
    ("Meteor", 18),
    ("Wave", 19),
    ("Pulse", 20),
    ("Larson", 21),
    ("Ripple", 22),
    ("Confetti", 23),
    ("Lava", 24),
    ("Plasma", 25),
    ("Heartbeat", 26),
]


class TestAnimationEnum:
    """Tests for Animation enum completeness and values."""

    def test_animation_count(self, sdk):
        """Should have exactly 27 animations."""
        animation_enum = sdk._bindings.connectorx.Animation

        # Count enum members (excluding special attributes)
        members = [m for m in dir(animation_enum)
                   if not m.startswith('_') and not m.startswith('name')
                   and not m.startswith('value')]

        # Filter to actual enum values
        enum_values = []
        for name in members:
            try:
                val = getattr(animation_enum, name)
                if hasattr(val, 'value'):
                    enum_values.append(name)
            except AttributeError:
                pass

        assert len(enum_values) == 27, \
            f"Expected 27 animations, found {len(enum_values)}: {enum_values}"

    @pytest.mark.parametrize("name,expected_value", EXPECTED_ANIMATIONS)
    def test_animation_value(self, sdk, name, expected_value):
        """Each animation should have the correct numeric value."""
        animation_enum = sdk._bindings.connectorx.Animation

        anim = getattr(animation_enum, name)
        assert anim.value == expected_value, \
            f"Animation {name} has value {anim.value}, expected {expected_value}"

    def test_common_animations_accessible(self, sdk):
        """Commonly used animations should be easily accessible."""
        anim = sdk._bindings.connectorx.Animation

        # These are the most commonly used animations
        assert hasattr(anim, 'Fill')
        assert hasattr(anim, 'Breathe')
        assert hasattr(anim, 'RainbowCycle')
        assert hasattr(anim, 'Chase')
        assert hasattr(anim, 'Fire')
        assert hasattr(anim, 'Sparkle')

    def test_new_animations_from_firmware(self, sdk):
        """New animations added from BuiltInAnimations.h should exist."""
        anim = sdk._bindings.connectorx.Animation

        # These were added when syncing with firmware BuiltInAnimations.h
        new_animations = [
            'Comet', 'Sparkle', 'Fire', 'Scanner', 'TheaterChase',
            'Twinkle', 'Meteor', 'Wave', 'Pulse', 'Larson',
            'Ripple', 'Confetti', 'Lava', 'Plasma', 'Heartbeat'
        ]

        for name in new_animations:
            assert hasattr(anim, name), f"Animation {name} should exist"


class TestAnimationColor:
    """Tests for AnimationColor structure."""

    def test_create_animation_color(self, sdk):
        """Should be able to create AnimationColor instances."""
        color = sdk._command.AnimationColor()
        assert hasattr(color, 'r')
        assert hasattr(color, 'g')
        assert hasattr(color, 'b')

    def test_set_color_values(self, sdk):
        """Should be able to set RGB values."""
        color = sdk._command.AnimationColor()
        color.r = 255
        color.g = 128
        color.b = 64

        assert color.r == 255
        assert color.g == 128
        assert color.b == 64

    def test_color_range(self, sdk):
        """Color values should handle full 0-255 range."""
        color = sdk._command.AnimationColor()

        # Test minimum
        color.r = 0
        color.g = 0
        color.b = 0
        assert color.r == 0
        assert color.g == 0
        assert color.b == 0

        # Test maximum
        color.r = 255
        color.g = 255
        color.b = 255
        assert color.r == 255
        assert color.g == 255
        assert color.b == 255


class TestAnimationWithIDCreator:
    """Tests for using animations with IDCreator (like the SDK does internally)."""

    def test_animation_name_hashing(self, sdk):
        """Animation names should produce consistent hashes via IDCreator."""
        id_creator = sdk._util.hashing.IDCreator

        # Hash some animation names
        breathe_hash = id_creator.createId("Breathe")
        chase_hash = id_creator.createId("Chase")
        fire_hash = id_creator.createId("Fire")

        # Hashes should be non-zero and different
        assert breathe_hash != 0
        assert chase_hash != 0
        assert fire_hash != 0
        assert breathe_hash != chase_hash
        assert chase_hash != fire_hash

    def test_hash_consistency(self, sdk):
        """Same input should always produce same hash."""
        id_creator = sdk._util.hashing.IDCreator

        hash1 = id_creator.createId("Sparkle")
        hash2 = id_creator.createId("Sparkle")

        assert hash1 == hash2, "Same input should produce same hash"


class TestMatrixTextScrollDirection:
    """Tests for MatrixTextScrollDirection enum."""

    def test_scroll_directions_exist(self, sdk):
        """Both scroll directions should be available."""
        scroll_dir = sdk._command.MatrixTextScrollDirection

        assert hasattr(scroll_dir, 'LEFT')
        assert hasattr(scroll_dir, 'RIGHT')

    def test_scroll_direction_values(self, sdk):
        """Scroll direction values should match C++ enum."""
        scroll_dir = sdk._command.MatrixTextScrollDirection

        assert scroll_dir.LEFT.value == 0
        assert scroll_dir.RIGHT.value == 1
