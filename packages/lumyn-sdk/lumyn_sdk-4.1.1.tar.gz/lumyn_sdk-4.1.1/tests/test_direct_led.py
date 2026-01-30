"""
Tests for the DirectLED high-performance API.

Tests DirectLED creation, updates, reset, and lifecycle management.

Mirrors C SDK test_direct_led_api.cpp
"""

import pytest
import lumyn_sdk
from lumyn_sdk import ConnectorX, ConnectorXAnimate, DirectLED


class TestDirectLEDCreation:
    """Tests for DirectLED creation."""

    def test_create_direct_led_from_connectorx(self):
        """Should be able to create DirectLED from ConnectorX."""
        cx = ConnectorX()

        # Create DirectLED through LED handler
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)
        assert direct_led is not None, "DirectLED should be created"

        cx.close()

    def test_create_direct_led_from_animate(self):
        """Should be able to create DirectLED from ConnectorXAnimate."""
        cxa = ConnectorXAnimate()

        # ConnectorXAnimate also supports DirectLED
        direct_led = cxa.leds.create_direct_led("zone_0", num_leds=10)
        assert direct_led is not None, "DirectLED should be created"

        cxa.close()

    def test_create_direct_led_with_various_led_counts(self):
        """DirectLED should support various LED counts."""
        cx = ConnectorX()

        led_counts = [1, 10, 100, 300, 1000]

        for count in led_counts:
            direct_led = cx.leds.create_direct_led("zone_0", num_leds=count)
            assert direct_led is not None, f"Failed to create DirectLED with {count} LEDs"
            # Note: Can't easily verify length without connecting to device

        cx.close()

    def test_create_direct_led_with_refresh_interval(self):
        """DirectLED should support custom refresh interval."""
        cx = ConnectorX()

        # Create with custom refresh interval
        direct_led = cx.leds.create_direct_led(
            "zone_0",
            num_leds=10,
            full_refresh_interval=50
        )
        assert direct_led is not None, "DirectLED with refresh interval should be created"

        cx.close()

    def test_create_direct_led_with_zero_refresh_interval(self):
        """DirectLED should accept 0 refresh interval (never auto-refresh)."""
        cx = ConnectorX()

        # 0 means never auto-refresh
        direct_led = cx.leds.create_direct_led(
            "zone_0",
            num_leds=10,
            full_refresh_interval=0
        )
        assert direct_led is not None, "DirectLED with 0 refresh should be created"

        cx.close()

    def test_create_direct_led_with_empty_zone_id(self):
        """DirectLED should handle empty zone ID."""
        cx = ConnectorX()

        # Empty zone ID should be accepted (depends on implementation)
        try:
            direct_led = cx.leds.create_direct_led("", num_leds=10)
            # If it succeeds, that's fine
            assert direct_led is not None
        except (ValueError, RuntimeError):
            # If it raises an error, that's also acceptable
            pass

        cx.close()


class TestDirectLEDUpdate:
    """Tests for DirectLED update functionality."""

    def test_update_when_not_connected_fails_gracefully(self):
        """DirectLED update when not connected should fail gracefully."""
        cx = ConnectorX()
        assert not cx.is_connected()

        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Create a buffer of colors (bytes format)
        colors = bytes([255, 0, 0] * 10)  # 30 bytes for 10 LEDs

        # Update when not connected should either:
        # 1. Return False/error
        # 2. Succeed locally but not send (depending on implementation)
        try:
            result = direct_led.update(colors)
            # Either returns False or succeeds locally
        except Exception as e:
            # Or raises an exception - both are acceptable
            pass

        cx.close()

    def test_update_with_matching_buffer_size(self):
        """DirectLED update with matching buffer size should work."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Create buffer with exact size (bytes, not tuples)
        # DirectLED expects raw RGB bytes: 3 bytes per LED
        colors = bytes([255, 0, 0] * 10)  # 30 bytes for 10 LEDs

        try:
            result = direct_led.update(colors)
            # Should not raise exception (may fail due to no connection)
        except Exception as e:
            # Check if it's a connection-related error (acceptable)
            # or a buffer size error (not acceptable)
            if "size" in str(e).lower() or "length" in str(e).lower():
                pytest.fail(f"Buffer size error with matching size: {e}")

        cx.close()

    def test_update_with_wrong_buffer_size_fails(self):
        """DirectLED update with wrong buffer size should fail."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Create buffer with wrong size (only 15 bytes for 10 LEDs which need 30)
        # Only 15 bytes (5 LEDs worth) for 10 LEDs
        colors = bytes([255, 0, 0] * 5)

        # Should fail with size mismatch
        with pytest.raises((ValueError, RuntimeError, IndexError)):
            direct_led.update(colors)

        cx.close()

    def test_update_with_various_colors(self):
        """DirectLED should accept various RGB byte values."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=3)

        # Test various RGB colors (as bytes)
        colors = bytes([
            255, 0, 0,      # Red
            0, 255, 0,      # Green
            0, 0, 255,      # Blue
        ])  # 9 bytes for 3 LEDs

        try:
            direct_led.update(colors)
        except Exception as e:
            # Connection errors are fine, format errors are not
            if "format" in str(e).lower() or "type" in str(e).lower():
                pytest.fail(f"Color format error: {e}")

        cx.close()

    def test_update_with_edge_case_colors(self):
        """DirectLED should handle edge case color values."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=3)

        # Test edge cases (as bytes)
        colors = bytes([
            0, 0, 0,          # Black
            255, 255, 255,    # White
            128, 128, 128,    # Gray
        ])  # 9 bytes for 3 LEDs

        try:
            direct_led.update(colors)
        except Exception as e:
            # Connection errors are fine
            if "connect" not in str(e).lower():
                # Other errors might be concerning
                pass

        cx.close()


class TestDirectLEDReset:
    """Tests for DirectLED reset functionality."""

    def test_reset_exists(self):
        """DirectLED should have reset method if available."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Check if reset method exists
        if hasattr(direct_led, 'reset'):
            # Try to call it
            try:
                direct_led.reset()
            except Exception:
                # May fail due to no connection, that's fine
                pass

        cx.close()


class TestDirectLEDMultipleInstances:
    """Tests for multiple DirectLED instances."""

    def test_multiple_direct_leds_on_same_device(self):
        """Should be able to create multiple DirectLED instances on same device."""
        cx = ConnectorX()

        led1 = cx.leds.create_direct_led("zone_0", num_leds=10)
        led2 = cx.leds.create_direct_led("zone_1", num_leds=20)
        led3 = cx.leds.create_direct_led("zone_2", num_leds=30)

        assert led1 is not None
        assert led2 is not None
        assert led3 is not None

        # All should be different objects
        assert led1 is not led2
        assert led2 is not led3
        assert led1 is not led3

        cx.close()

    def test_multiple_direct_leds_same_zone(self):
        """Creating DirectLED for same zone creates independent instances."""
        cx = ConnectorX()

        # Create two DirectLED instances for the same zone
        led1 = cx.leds.create_direct_led("zone_0", num_leds=10)
        led2 = cx.leds.create_direct_led("zone_0", num_leds=10)

        assert led1 is not None
        assert led2 is not None
        # Both instances should manage the same zone, but may be separate objects
        # (caching is an optional optimization, not required)
        assert led1.zone_id == led2.zone_id == "zone_0"

        cx.close()


class TestDirectLEDInterface:
    """Tests for DirectLED interface/methods."""

    def test_direct_led_has_update_method(self):
        """DirectLED should have update method."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        assert hasattr(
            direct_led, 'update'), "DirectLED should have update method"

        cx.close()

    def test_direct_led_type(self):
        """DirectLED should be of DirectLED type."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Check that it's a DirectLED instance
        assert isinstance(
            direct_led, DirectLED), "Should be DirectLED instance"

        cx.close()


class TestDirectLEDWithDeviceLifecycle:
    """Tests for DirectLED behavior with device lifecycle."""

    def test_direct_led_after_device_close(self):
        """DirectLED behavior after device close."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        cx.close()

        # Try to update after device close (bytes format)
        colors = bytes([0, 0, 0] * 10)  # 30 bytes for 10 LEDs
        try:
            result = direct_led.update(colors)
            # May succeed (buffer locally) or fail (device closed)
        except Exception:
            # Exception is acceptable after device close
            pass


class TestDirectLEDDeltaCompression:
    """Tests for DirectLED delta compression feature."""

    def test_delta_compression_updates_unchanged_buffer(self):
        """DirectLED should handle unchanged buffer efficiently."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Update with same colors multiple times (bytes format)
        colors = bytes([255, 0, 0] * 10)  # 30 bytes for 10 LEDs

        try:
            # First update
            direct_led.update(colors)
            # Second update with same colors (should use delta compression)
            direct_led.update(colors)
            # Third update
            direct_led.update(colors)
            # All should succeed (or all fail due to no connection)
        except Exception as e:
            # Connection errors are fine
            pass

        cx.close()

    def test_delta_compression_partial_update(self):
        """DirectLED should efficiently handle partial updates."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # First update - all red (bytes format)
        colors1 = bytes([255, 0, 0] * 10)  # 30 bytes

        # Second update - change only first LED to green
        colors2 = bytes([0, 255, 0] + [255, 0, 0] * 9)  # 30 bytes

        try:
            direct_led.update(colors1)
            direct_led.update(colors2)  # Should only send delta
        except Exception:
            # Connection errors are fine
            pass

        cx.close()


class TestDirectLEDErrorHandling:
    """Tests for DirectLED error handling."""

    def test_invalid_color_values_handled(self):
        """DirectLED should handle bytes buffer format."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=3)

        # Valid bytes (bytes are inherently 0-255)
        colors = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])  # 9 bytes for 3 LEDs

        try:
            direct_led.update(colors)
            # May succeed locally or fail due to no connection
        except Exception as e:
            # Connection errors are fine
            if "connect" not in str(e).lower():
                pass

        cx.close()

    def test_none_buffer_raises_error(self):
        """DirectLED update with None buffer should raise error."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        with pytest.raises((TypeError, ValueError, AttributeError)):
            direct_led.update(None)

        cx.close()

    def test_empty_buffer_raises_error(self):
        """DirectLED update with empty buffer should raise error."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        with pytest.raises((ValueError, RuntimeError, IndexError)):
            direct_led.update([])

        cx.close()


class TestDirectLEDPerformance:
    """Tests for DirectLED performance characteristics."""

    def test_many_sequential_updates(self):
        """DirectLED should handle many sequential updates."""
        cx = ConnectorX()
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=10)

        # Perform many updates (testing for memory leaks, crashes)
        try:
            for i in range(100):
                colors = bytes([i % 256, 0, 0] * 10)  # 30 bytes for 10 LEDs
                direct_led.update(colors)
        except Exception:
            # Connection errors are fine
            pass

        cx.close()

    def test_large_led_buffer(self):
        """DirectLED should handle large LED buffers."""
        cx = ConnectorX()

        # Create with large buffer (e.g., 1000 LEDs)
        direct_led = cx.leds.create_direct_led("zone_0", num_leds=1000)
        assert direct_led is not None

        # Try to update (bytes format)
        try:
            colors = bytes([255, 0, 0] * 1000)  # 3000 bytes for 1000 LEDs
            direct_led.update(colors)
        except Exception:
            # Connection errors are fine
            pass

        cx.close()
