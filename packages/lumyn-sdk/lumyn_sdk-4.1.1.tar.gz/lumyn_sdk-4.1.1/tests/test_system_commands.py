"""
Tests for system command buffer serialization.

Verifies that system commands (ClearStatusFlag, SetAssignedId, RestartDevice)
are serialized correctly for firmware consumption.
"""

from .test_helpers import (
    COMMAND_HEADER_SIZE,
    CommandType,
    SystemCommandType,
    parse_command_header,
)
import pytest
import struct
import sys
import os


class TestClearStatusFlagCommand:
    """Tests for ClearStatusFlag command buffer format."""

    def test_buffer_size(self, command_builder):
        """ClearStatusFlag should have CommandHeader + 4-byte mask."""
        buffer = command_builder.buildClearStatusFlag(flags=0xFFFFFFFF)

        expected_size = COMMAND_HEADER_SIZE + 4  # uint32_t mask
        assert len(buffer) == expected_size, \
            f"Buffer size {len(buffer)} != expected {expected_size}"

    def test_command_header(self, command_builder):
        """ClearStatusFlag should have correct CommandHeader."""
        buffer = command_builder.buildClearStatusFlag(flags=0)

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.SYSTEM
        assert header['subtype'] == SystemCommandType.CLEAR_STATUS_FLAG

    def test_flags_serialization(self, command_builder):
        """Flags mask should be serialized as little-endian uint32_t."""
        test_flags = 0xDEADBEEF
        buffer = command_builder.buildClearStatusFlag(flags=test_flags)

        # Extract the flags from the buffer (after CommandHeader)
        flags, = struct.unpack(
            '<I', buffer[COMMAND_HEADER_SIZE:COMMAND_HEADER_SIZE + 4])
        assert flags == test_flags, f"Flags {flags:#x} != expected {test_flags:#x}"

    def test_specific_flag_bits(self, command_builder):
        """Test individual flag bits are preserved."""
        # Test clearing just bit 0
        buffer = command_builder.buildClearStatusFlag(flags=0x01)
        flags, = struct.unpack('<I', buffer[COMMAND_HEADER_SIZE:])
        assert flags == 0x01

        # Test clearing multiple bits
        buffer = command_builder.buildClearStatusFlag(
            flags=0x15)  # bits 0, 2, 4
        flags, = struct.unpack('<I', buffer[COMMAND_HEADER_SIZE:])
        assert flags == 0x15


class TestSetAssignedIdCommand:
    """Tests for SetAssignedId command buffer format."""

    def test_command_header(self, command_builder):
        """SetAssignedId should have correct CommandHeader."""
        buffer = command_builder.buildSetAssignedId(assigned_id="test_device")

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.SYSTEM
        assert header['subtype'] == SystemCommandType.SET_ASSIGNED_ID

    def test_id_is_serialized(self, command_builder):
        """Assigned ID string should be present in buffer."""
        test_id = "my_connector_x"
        buffer = command_builder.buildSetAssignedId(assigned_id=test_id)

        # The ID should appear in the buffer after the header
        # Note: The C++ uses a 24-char buffer for the ID
        payload = buffer[COMMAND_HEADER_SIZE:]

        # Check that the test_id appears at the start of the payload
        id_bytes = payload[:len(test_id)]
        assert id_bytes == test_id.encode('ascii'), \
            f"ID not found at expected location"

    def test_empty_id(self, command_builder):
        """Empty ID should be handled gracefully."""
        buffer = command_builder.buildSetAssignedId(assigned_id="")

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.SYSTEM
        # Buffer should still be valid
        assert len(buffer) > COMMAND_HEADER_SIZE


class TestRestartDeviceCommand:
    """Tests for RestartDevice command buffer format."""

    def test_command_header(self, command_builder):
        """RestartDevice should have correct CommandHeader."""
        buffer = command_builder.buildRestartDevice()

        header = parse_command_header(buffer)
        assert header['type'] == CommandType.SYSTEM
        assert header['subtype'] == SystemCommandType.RESTART_DEVICE

    def test_buffer_size(self, command_builder):
        """RestartDevice should have minimal size (header + restart data)."""
        buffer = command_builder.buildRestartDevice()

        # RestartDevice has a delayMs field (uint16_t)
        expected_min_size = COMMAND_HEADER_SIZE + 2
        assert len(buffer) >= expected_min_size, \
            f"Buffer size {len(buffer)} < expected minimum {expected_min_size}"


class TestCommandTypeValues:
    """Verify command type enum values match firmware expectations."""

    def test_command_type_values(self, sdk):
        """CommandType enum values should match C++ definitions."""
        assert sdk._command.CommandType.System.value == 0
        assert sdk._command.CommandType.LED.value == 1
        assert sdk._command.CommandType.Device.value == 2

    def test_led_command_type_values(self, sdk):
        """LEDCommandType enum values should match C++ definitions."""
        led_cmd = sdk._command.LEDCommandType

        assert led_cmd.SetAnimation.value == 0
        assert led_cmd.SetAnimationGroup.value == 1
        assert led_cmd.SetColor.value == 2
        assert led_cmd.SetColorGroup.value == 3
        assert led_cmd.SetAnimationSequence.value == 4
        assert led_cmd.SetAnimationSequenceGroup.value == 5
        assert led_cmd.SetBitmap.value == 6
        assert led_cmd.SetBitmapGroup.value == 7
        assert led_cmd.SetMatrixText.value == 8
        assert led_cmd.SetMatrixTextGroup.value == 9
        assert led_cmd.SetDirectBuffer.value == 10

    def test_system_command_type_values(self, sdk):
        """SystemCommandType enum values should match C++ definitions."""
        sys_cmd = sdk._command.SystemCommandType

        assert sys_cmd.ClearStatusFlag.value == 0
        assert sys_cmd.SetAssignedId.value == 1
        assert sys_cmd.RestartDevice.value == 2
