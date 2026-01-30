"""
Tests for ConnectorX device class and related handlers.

Verifies that the main device API is correctly exposed.
"""

import pytest


class TestConnectorXClass:
    """Tests for ConnectorX class."""

    def test_connectorx_internal_exists(self, sdk):
        """ConnectorXInternal class should be available."""
        assert hasattr(sdk._bindings.connectorx, 'ConnectorXInternal')

    def test_create_connectorx_internal(self, sdk):
        """Should be able to create ConnectorXInternal instance."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        assert cx is not None

    def test_led_methods_on_device(self, sdk):
        """ConnectorXInternal should have LED control methods directly."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        # LED methods are directly on the device, not via leds() commander
        assert hasattr(cx, 'SetColor')
        assert hasattr(cx, 'SetGroupColor')
        assert hasattr(cx, 'SetAnimation')
        assert hasattr(cx, 'SetImageSequence')
        assert hasattr(cx, 'SetText')

    def test_matrix_methods_on_device(self, sdk):
        """ConnectorXInternal should have matrix control methods directly."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        # Matrix text method is directly on the device
        assert hasattr(cx, 'SetText')

    def test_get_events_method(self, sdk):
        """ConnectorXInternal should have GetEvents() method."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        assert hasattr(cx, 'GetEvents')

    def test_get_latest_module_data_method(self, sdk):
        """ConnectorXInternal should have GetLatestModuleData() method."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        assert hasattr(cx, 'GetLatestModuleData')

    def test_request_config_method(self, sdk):
        """ConnectorXInternal should have RequestConfig() method."""
        cx = sdk._bindings.connectorx.ConnectorXInternal()
        assert hasattr(cx, 'RequestConfig')


class TestPythonWrapperConnectorX:
    """Tests for the Python wrapper ConnectorX class."""

    def test_wrapper_exists(self, sdk):
        """High-level ConnectorX wrapper should exist."""
        # The Python wrapper is in lumyn_sdk directly
        import lumyn_sdk
        assert hasattr(lumyn_sdk, 'ConnectorX')

    def test_wrapper_creation(self, sdk):
        """Should be able to create ConnectorX wrapper instance."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert cx is not None

    def test_wrapper_has_connect(self, sdk):
        """ConnectorX wrapper should have connect method."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert hasattr(cx, 'connect')

    def test_wrapper_has_is_connected(self, sdk):
        """ConnectorX wrapper should have is_connected method."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert hasattr(cx, 'is_connected')

    def test_wrapper_has_led_handler(self, sdk):
        """ConnectorX wrapper should have led_handler property."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert hasattr(cx, 'led_handler')

    def test_wrapper_has_module_handler(self, sdk):
        """ConnectorX wrapper should have module_handler property."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert hasattr(cx, 'module_handler')

    def test_wrapper_not_connected_initially(self, sdk):
        """ConnectorX should not be connected before connect() is called."""
        import lumyn_sdk
        cx = lumyn_sdk.ConnectorX()
        assert cx.is_connected() == False
