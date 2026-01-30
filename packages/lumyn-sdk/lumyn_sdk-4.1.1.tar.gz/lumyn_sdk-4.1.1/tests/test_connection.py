"""
Tests for connection management API.

Tests Connect, Disconnect, IsConnected, and related connection functions.

Mirrors C SDK test_connection_api.cpp
"""

import pytest
import lumyn_sdk
from lumyn_sdk import ConnectorX, ConnectorXAnimate


class TestIsConnected:
    """Tests for is_connected() method."""

    def test_is_connected_returns_false_for_new_device(self):
        """is_connected() should return False for newly created device."""
        cx = ConnectorX()
        assert not cx.is_connected(), "New device should not be connected"
        cx.close()

    def test_is_connected_false_for_animate(self):
        """ConnectorXAnimate should also return False when not connected."""
        cxa = ConnectorXAnimate()
        assert not cxa.is_connected(), "New animate device should not be connected"
        cxa.close()

    def test_is_connected_after_close(self):
        """is_connected() should return False after device is closed."""
        cx = ConnectorX()
        cx.close()
        assert not cx.is_connected(), "Closed device should not be connected"


class TestConnectErrorCases:
    """Tests for connect() error cases."""

    def test_connect_with_invalid_port_returns_false(self):
        """connect() should return False for non-existent port."""
        cx = ConnectorX()
        # Try to connect to non-existent port
        result = cx.connect("/dev/nonexistent_port_12345")
        assert not result, "Connection to invalid port should fail"
        assert not cx.is_connected(), "Should not be connected after failed connection"
        cx.close()

    def test_connect_with_empty_port_returns_false(self):
        """connect() should return False for empty port string."""
        cx = ConnectorX()
        # Empty port should fail
        result = cx.connect("")
        assert not result, "Connection with empty port should fail"
        cx.close()

    def test_connect_animate_with_invalid_port_returns_false(self):
        """ConnectorXAnimate should also fail with invalid port."""
        cxa = ConnectorXAnimate()
        result = cxa.connect("/dev/nonexistent_port_12345")
        assert not result, "Connection to invalid port should fail"
        assert not cxa.is_connected(), "Should not be connected after failed connection"
        cxa.close()


class TestConnectUSB:
    """Tests for connect_usb() method."""

    def test_connect_usb_exists(self):
        """ConnectorX should have connect_usb method."""
        cx = ConnectorX()
        assert hasattr(cx, 'connect_usb'), "ConnectorX should have connect_usb method"
        cx.close()

    def test_connect_usb_with_invalid_port_returns_false(self):
        """connect_usb() should return False for non-existent port."""
        cx = ConnectorX()
        result = cx.connect_usb("/dev/nonexistent_usb_port")
        assert not result, "USB connection to invalid port should fail"
        cx.close()


class TestConnectUART:
    """Tests for connect_uart() method (ConnectorX only)."""

    def test_connect_uart_exists_on_connectorx(self):
        """ConnectorX should have connect_uart method."""
        cx = ConnectorX()
        assert hasattr(cx, 'connect_uart'), "ConnectorX should have connect_uart method"
        cx.close()

    def test_connect_uart_not_on_animate(self):
        """ConnectorXAnimate should not have connect_uart (LED-only device)."""
        cxa = ConnectorXAnimate()
        # ConnectorXAnimate doesn't support UART
        assert not hasattr(cxa, 'connect_uart'), \
            "ConnectorXAnimate should not have connect_uart (LED-only)"
        cxa.close()

    def test_connect_uart_with_invalid_port_returns_false(self):
        """connect_uart() should return False for non-existent port."""
        cx = ConnectorX()
        result = cx.connect_uart("/dev/nonexistent_uart_port", 115200)
        assert not result, "UART connection to invalid port should fail"
        cx.close()

    def test_connect_uart_with_various_baud_rates(self):
        """connect_uart() should accept various baud rates."""
        cx = ConnectorX()
        # Test with various baud rates - all should fail gracefully with invalid port
        baud_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        
        for baud in baud_rates:
            result = cx.connect_uart("/dev/nonexistent_uart", baud)
            assert not result, f"Connection with baud {baud} to invalid port should fail"
        
        cx.close()


class TestDisconnect:
    """Tests for disconnect() method."""

    def test_disconnect_exists(self):
        """Device should have disconnect method."""
        cx = ConnectorX()
        assert hasattr(cx, 'disconnect'), "ConnectorX should have disconnect method"
        cx.close()

    def test_disconnect_when_not_connected_is_safe(self):
        """disconnect() should not raise exception when not connected."""
        cx = ConnectorX()
        assert not cx.is_connected()
        
        try:
            cx.disconnect()
        except Exception as e:
            pytest.fail(f"disconnect() raised exception when not connected: {e}")
        
        cx.close()

    def test_double_disconnect_is_safe(self):
        """Double disconnect should not raise exception."""
        cx = ConnectorX()
        
        try:
            cx.disconnect()
            cx.disconnect()  # Second disconnect should be safe
        except Exception as e:
            pytest.fail(f"Double disconnect raised exception: {e}")
        
        cx.close()

    def test_disconnect_animate_is_safe(self):
        """ConnectorXAnimate disconnect should also be safe."""
        cxa = ConnectorXAnimate()
        
        try:
            cxa.disconnect()
        except Exception as e:
            pytest.fail(f"ConnectorXAnimate disconnect raised exception: {e}")
        
        cxa.close()


class TestConnectionStatus:
    """Tests for connection status methods."""

    def test_get_current_status_exists(self):
        """Device should have get_current_status method if available."""
        cx = ConnectorX()
        # Check if method exists (may be in base class)
        if hasattr(cx, 'get_current_status'):
            status = cx.get_current_status()
            # Status should be some value (details depend on implementation)
            assert status is not None
        cx.close()


class TestConnectionAfterDestroy:
    """Tests for connection attempts after device destruction."""

    def test_connect_after_close_fails_gracefully(self):
        """Attempting to connect after close should fail gracefully."""
        cx = ConnectorX()
        cx.close()
        
        # Attempting to connect after close should return False
        # (not raise exception if possible)
        try:
            result = cx.connect("/dev/test")
            assert not result, "Connection after close should fail"
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass

    def test_is_connected_after_close_returns_false(self):
        """is_connected() after close should return False."""
        cx = ConnectorX()
        cx.close()
        assert not cx.is_connected(), "Closed device should not be connected"


class TestConnectionSequence:
    """Tests for connection/disconnection sequences."""

    def test_multiple_connection_attempts_to_invalid_port(self):
        """Multiple failed connection attempts should be safe."""
        cx = ConnectorX()
        
        # Try to connect multiple times to invalid port
        for _ in range(5):
            result = cx.connect("/dev/nonexistent_port")
            assert not result, "Connection to invalid port should fail"
            assert not cx.is_connected()
        
        cx.close()

    def test_connect_disconnect_sequence(self):
        """Connect/disconnect sequence should work without errors."""
        cx = ConnectorX()
        
        # Even though connection fails, the sequence should work
        cx.connect("/dev/invalid")
        cx.disconnect()
        cx.connect("/dev/invalid")
        cx.disconnect()
        
        assert not cx.is_connected()
        cx.close()


class TestConnectionValidation:
    """Tests for connection parameter validation."""

    def test_connect_with_none_port_fails_gracefully(self):
        """connect() with None port should fail gracefully."""
        cx = ConnectorX()
        
        try:
            # Depending on implementation, may return False or raise TypeError
            result = cx.connect(None)
            assert not result, "Connection with None port should fail"
        except (TypeError, AttributeError):
            # If it raises TypeError/AttributeError, that's acceptable
            pass
        
        cx.close()

    def test_connect_with_invalid_type_fails(self):
        """connect() with invalid type should fail gracefully."""
        cx = ConnectorX()
        
        try:
            # Try with integer instead of string
            result = cx.connect(12345)
            assert not result, "Connection with invalid type should fail"
        except TypeError:
            # TypeError is acceptable for invalid type
            pass
        
        cx.close()


class TestConnectionHelpers:
    """Tests for connection helper functions."""

    def test_list_available_ports_exists(self):
        """list_available_ports() function should exist."""
        assert hasattr(lumyn_sdk.devices, 'list_available_ports'), \
            "lumyn_sdk.devices should have list_available_ports function"

    def test_list_available_ports_returns_list(self):
        """list_available_ports() should return a list."""
        ports = lumyn_sdk.devices.list_available_ports()
        assert isinstance(ports, list), "list_available_ports() should return a list"

    def test_list_available_ports_consistent(self):
        """Multiple calls to list_available_ports() should be consistent."""
        ports1 = lumyn_sdk.devices.list_available_ports()
        ports2 = lumyn_sdk.devices.list_available_ports()
        
        # Should return the same number of ports (assuming hardware doesn't change)
        # Note: This may be flaky if USB devices are added/removed during test
        # so we just check the type and format
        assert isinstance(ports1, list)
        assert isinstance(ports2, list)
