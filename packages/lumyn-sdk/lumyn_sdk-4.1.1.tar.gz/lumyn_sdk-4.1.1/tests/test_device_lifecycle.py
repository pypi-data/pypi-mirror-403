"""
Tests for device creation and destruction lifecycle.

Tests the full lifecycle of ConnectorX and ConnectorXAnimate devices,
including proper initialization and cleanup.

Mirrors C SDK test_device_lifecycle.cpp
"""

import pytest
import lumyn_sdk
from lumyn_sdk import ConnectorX, ConnectorXAnimate


class TestConnectorXCreation:
    """Tests for ConnectorX device creation."""

    def test_create_connectorx_succeeds(self):
        """Should be able to create ConnectorX instance."""
        cx = ConnectorX()
        assert cx is not None, "ConnectorX instance should not be None"

    def test_connectorx_has_internal_state(self):
        """ConnectorX should have internal state after creation."""
        cx = ConnectorX()
        # Check that internal state exists (even if None initially)
        assert hasattr(
            cx, '_internal'), "ConnectorX should have _internal attribute"

    def test_connectorx_has_led_handler(self):
        """ConnectorX should have LED handler after creation."""
        cx = ConnectorX()
        assert hasattr(cx, 'leds'), "ConnectorX should have leds attribute"
        assert cx.leds is not None, "LED handler should be initialized"

    def test_connectorx_has_module_handler(self):
        """ConnectorX should have module handler after creation."""
        cx = ConnectorX()
        assert hasattr(
            cx, 'modules'), "ConnectorX should have modules attribute"
        assert cx.modules is not None, "Module handler should be initialized"

    def test_connectorx_has_module_dispatcher(self):
        """ConnectorX should have module dispatcher after creation."""
        cx = ConnectorX()
        assert hasattr(cx, 'get_module_dispatcher'), \
            "ConnectorX should have get_module_dispatcher method"
        dispatcher = cx.get_module_dispatcher()
        assert dispatcher is not None, "Module dispatcher should be initialized"


class TestConnectorXAnimateCreation:
    """Tests for ConnectorXAnimate device creation."""

    def test_create_connectorx_animate_succeeds(self):
        """Should be able to create ConnectorXAnimate instance."""
        cxa = ConnectorXAnimate()
        assert cxa is not None, "ConnectorXAnimate instance should not be None"

    def test_connectorx_animate_has_internal_state(self):
        """ConnectorXAnimate should have internal state after creation."""
        cxa = ConnectorXAnimate()
        assert hasattr(cxa, '_internal'), \
            "ConnectorXAnimate should have _internal attribute"

    def test_connectorx_animate_has_led_handler(self):
        """ConnectorXAnimate should have LED handler after creation."""
        cxa = ConnectorXAnimate()
        assert hasattr(
            cxa, 'leds'), "ConnectorXAnimate should have leds attribute"
        assert cxa.leds is not None, "LED handler should be initialized"

    def test_connectorx_animate_no_module_handler(self):
        """ConnectorXAnimate should not have module handler (LED-only device)."""
        cxa = ConnectorXAnimate()
        # ConnectorXAnimate is LED-only, should not have modules
        assert not hasattr(cxa, 'modules') or cxa.modules is None, \
            "ConnectorXAnimate should not have modules (LED-only device)"


class TestDeviceDestruction:
    """Tests for device cleanup and destruction."""

    def test_connectorx_close_is_safe(self):
        """Closing ConnectorX should not raise exceptions."""
        cx = ConnectorX()
        try:
            cx.close()
        except Exception as e:
            pytest.fail(f"ConnectorX.close() raised exception: {e}")

    def test_connectorx_animate_close_is_safe(self):
        """Closing ConnectorXAnimate should not raise exceptions."""
        cxa = ConnectorXAnimate()
        try:
            cxa.close()
        except Exception as e:
            pytest.fail(f"ConnectorXAnimate.close() raised exception: {e}")

    def test_double_close_connectorx_is_safe(self):
        """Double closing ConnectorX should not crash."""
        cx = ConnectorX()
        cx.close()
        try:
            cx.close()  # Second close should be safe
        except Exception as e:
            pytest.fail(f"Double close raised exception: {e}")

    def test_double_close_connectorx_animate_is_safe(self):
        """Double closing ConnectorXAnimate should not crash."""
        cxa = ConnectorXAnimate()
        cxa.close()
        try:
            cxa.close()  # Second close should be safe
        except Exception as e:
            pytest.fail(f"Double close raised exception: {e}")

    def test_connectorx_with_context_manager(self):
        """ConnectorX should work as a context manager if supported."""
        # Check if context manager is implemented
        cx = ConnectorX()
        if hasattr(cx, '__enter__') and hasattr(cx, '__exit__'):
            with ConnectorX() as device:
                assert device is not None


class TestMultipleInstances:
    """Tests for creating multiple device instances."""

    def test_multiple_connectorx_instances_can_coexist(self):
        """Multiple ConnectorX instances should be able to exist simultaneously."""
        cx1 = ConnectorX()
        cx2 = ConnectorX()
        cx3 = ConnectorX()

        # All should be valid
        assert cx1 is not None
        assert cx2 is not None
        assert cx3 is not None

        # All should be different objects
        assert cx1 is not cx2
        assert cx2 is not cx3
        assert cx1 is not cx3

        # Clean up
        cx3.close()
        cx2.close()
        cx1.close()

    def test_mixed_device_types_can_coexist(self):
        """ConnectorX and ConnectorXAnimate should be able to coexist."""
        cx = ConnectorX()
        cxa = ConnectorXAnimate()

        assert cx is not None
        assert cxa is not None
        assert cx is not cxa

        cxa.close()
        cx.close()

    def test_many_devices_can_be_created(self):
        """Should be able to create many device instances."""
        devices = []
        num_devices = 10

        for i in range(num_devices):
            cx = ConnectorX()
            assert cx is not None, f"Failed to create device {i}"
            devices.append(cx)

        # Verify all are unique
        for i in range(len(devices)):
            for j in range(i + 1, len(devices)):
                assert devices[i] is not devices[j], \
                    f"Devices {i} and {j} are the same object"

        # Clean up
        for cx in devices:
            cx.close()


class TestInitialState:
    """Tests for initial device state."""

    def test_new_connectorx_is_not_connected(self):
        """New ConnectorX should not be connected."""
        cx = ConnectorX()
        assert not cx.is_connected(), "New device should not be connected"
        cx.close()

    def test_new_connectorx_animate_is_not_connected(self):
        """New ConnectorXAnimate should not be connected."""
        cxa = ConnectorXAnimate()
        assert not cxa.is_connected(), "New device should not be connected"
        cxa.close()

    def test_connectorx_properties_are_initialized(self):
        """ConnectorX properties should be properly initialized."""
        cx = ConnectorX()

        # Check that key properties are accessible
        assert hasattr(cx, 'leds')
        assert hasattr(cx, 'modules')
        assert hasattr(cx, 'is_connected')
        assert hasattr(cx, 'connect')
        assert hasattr(cx, 'close')

        cx.close()

    def test_connectorx_animate_properties_are_initialized(self):
        """ConnectorXAnimate properties should be properly initialized."""
        cxa = ConnectorXAnimate()

        # Check that key properties are accessible
        assert hasattr(cxa, 'leds')
        assert hasattr(cxa, 'is_connected')
        assert hasattr(cxa, 'connect')
        assert hasattr(cxa, 'close')

        cxa.close()


class TestReinitialization:
    """Tests for reinitializing destroyed devices."""

    def test_can_create_new_device_after_close(self):
        """Should be able to create new device after closing previous one."""
        cx1 = ConnectorX()
        assert cx1 is not None
        cx1.close()

        # Create new instance - should work fine
        cx2 = ConnectorX()
        assert cx2 is not None
        assert cx2 is not cx1  # Different object
        cx2.close()


class TestDeviceTypes:
    """Tests for device type hierarchy."""

    def test_connectorx_is_instance_of_base(self):
        """ConnectorX should be an instance of ConnectorXBase."""
        from lumyn_sdk.devices.connectorx_base import ConnectorXBase
        cx = ConnectorX()
        assert isinstance(cx, ConnectorXBase), \
            "ConnectorX should be instance of ConnectorXBase"
        cx.close()

    def test_connectorx_animate_is_instance_of_base(self):
        """ConnectorXAnimate should be an instance of ConnectorXBase."""
        from lumyn_sdk.devices.connectorx_base import ConnectorXBase
        cxa = ConnectorXAnimate()
        assert isinstance(cxa, ConnectorXBase), \
            "ConnectorXAnimate should be instance of ConnectorXBase"
        cxa.close()

    def test_connectorx_and_animate_are_different_types(self):
        """ConnectorX and ConnectorXAnimate should be different types."""
        cx = ConnectorX()
        cxa = ConnectorXAnimate()

        assert type(cx) != type(cxa), \
            "ConnectorX and ConnectorXAnimate should be different types"

        cxa.close()
        cx.close()
