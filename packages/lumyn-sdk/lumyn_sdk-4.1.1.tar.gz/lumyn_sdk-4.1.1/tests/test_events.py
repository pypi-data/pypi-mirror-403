"""
Tests for event types and event handling.

Verifies that event-related types are correctly exposed.
"""

import pytest


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types_exist(self, sdk):
        """Common event types should be available."""
        event_type = sdk._event.EventType

        # Check for common event types
        assert hasattr(event_type, 'Connected')
        assert hasattr(event_type, 'Disconnected')
        assert hasattr(event_type, 'Error')
        assert hasattr(event_type, 'HeartBeat')

    def test_event_type_is_enum(self, sdk):
        """EventType should behave like an enum."""
        event_type = sdk._event.EventType

        # Should be able to access values
        connected = event_type.Connected
        assert hasattr(connected, 'value')


class TestEventConnectionType:
    """Tests for EventConnectionType enum."""

    def test_event_connection_type_exists(self, sdk):
        """EventConnectionType should be available in event submodule."""
        assert hasattr(sdk._event, 'ConnectionType')


class TestEventStructure:
    """Tests for Event structure."""

    def test_event_class_exists(self, sdk):
        """Event class should be available."""
        assert hasattr(sdk._event, 'Event')


class TestEventCallback:
    """Tests for IEventCallback interface."""

    def test_callback_interface_exists(self, sdk):
        """IEventCallback interface should be available in interfaces submodule."""
        assert hasattr(sdk.interfaces.i_event_callback, 'IEventCallback')
