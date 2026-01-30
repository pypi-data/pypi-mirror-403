"""
Test fixtures for Lumyn SDK tests.

Provides common fixtures and utilities for testing command serialization,
transmission formats, and buffer verification.
"""

import pytest
import struct


# ============================================================================
# Struct Size Constants (matching C++ packed structures)
# ============================================================================

# From common/include/lumyn/domain/command/Command.h
# CommandType (1 byte) + union{ledType, systemType} (1 byte)
COMMAND_HEADER_SIZE = 2

# From common/include/lumyn/domain/command/led/LEDCommand.h
ANIMATION_COLOR_SIZE = 3  # r, g, b (3 bytes)
# zoneId(2) + animationId(2) + delay(2) + color(3) + flags(1)
SET_ANIMATION_DATA_SIZE = 10
SET_COLOR_DATA_SIZE = 5  # zoneId(2) + color(3)
SET_ANIMATION_SEQUENCE_DATA_SIZE = 4  # zoneId(2) + sequenceId(2)
SET_BITMAP_DATA_SIZE = 8  # zoneId(2) + bitmapId(2) + color(3) + flags(1)

# From common/include/lumyn/domain/transmission/Transmission.h
# type(1) + dataLength(4) + packetCount(2) + flags(1)
TRANSMISSION_HEADER_SIZE = 8


# ============================================================================
# Enum Values (matching C++ enums)
# ============================================================================

class CommandType:
    """CommandType enum values - from Command.h"""
    SYSTEM = 0
    LED = 1
    DEVICE = 2


class LEDCommandType:
    """LEDCommandType enum values - from LEDCommandType.h"""
    SET_ANIMATION = 0
    SET_ANIMATION_GROUP = 1
    SET_COLOR = 2
    SET_COLOR_GROUP = 3
    SET_ANIMATION_SEQUENCE = 4
    SET_ANIMATION_SEQUENCE_GROUP = 5
    SET_BITMAP = 6
    SET_BITMAP_GROUP = 7
    SET_MATRIX_TEXT = 8
    SET_MATRIX_TEXT_GROUP = 9
    SET_DIRECT_BUFFER = 10


class SystemCommandType:
    """SystemCommandType enum values - from SystemCommandType.h"""
    CLEAR_STATUS_FLAG = 0
    SET_ASSIGNED_ID = 1
    RESTART_DEVICE = 2


class TransmissionType:
    """TransmissionType enum values - from TransmissionType.h"""
    REQUEST = 0
    RESPONSE = 1
    EVENT = 2
    COMMAND = 3
    FILE = 4
    MODULE_DATA = 5


# ============================================================================
# Helper Functions for Buffer Parsing
# ============================================================================

def parse_command_header(buffer: bytes) -> dict:
    """
    Parse a CommandHeader from the start of a buffer.

    Layout:
        - type: uint8_t (CommandType)
        - subtype: uint8_t (LEDCommandType or SystemCommandType based on type)
    """
    if len(buffer) < COMMAND_HEADER_SIZE:
        raise ValueError(
            f"Buffer too small for CommandHeader: {len(buffer)} < {COMMAND_HEADER_SIZE}")

    command_type, subtype = struct.unpack('<BB', buffer[:COMMAND_HEADER_SIZE])
    return {
        'type': command_type,
        'subtype': subtype,
        'raw': buffer[:COMMAND_HEADER_SIZE]
    }


def parse_animation_color(buffer: bytes, offset: int = 0) -> dict:
    """
    Parse an AnimationColor from a buffer.

    Layout:
        - r: uint8_t
        - g: uint8_t  
        - b: uint8_t
    """
    if len(buffer) < offset + ANIMATION_COLOR_SIZE:
        raise ValueError(
            f"Buffer too small for AnimationColor at offset {offset}")

    r, g, b = struct.unpack(
        '<BBB', buffer[offset:offset + ANIMATION_COLOR_SIZE])
    return {'r': r, 'g': g, 'b': b}


def parse_set_animation_data(buffer: bytes, offset: int = 0) -> dict:
    """
    Parse SetAnimationData from a buffer.

    Layout (10 bytes total):
        - zoneId: uint16_t
        - animationId: uint16_t
        - delay: uint16_t
        - color: AnimationColor (3 bytes)
        - flags: uint8_t (bit 0 = reversed, bit 1 = oneShot)
    """
    if len(buffer) < offset + SET_ANIMATION_DATA_SIZE:
        raise ValueError(
            f"Buffer too small for SetAnimationData at offset {offset}")

    zone_id, animation_id, delay = struct.unpack(
        '<HHH', buffer[offset:offset + 6])
    color = parse_animation_color(buffer, offset + 6)
    flags = buffer[offset + 9]

    return {
        'zoneId': zone_id,
        'animationId': animation_id,
        'delay': delay,
        'color': color,
        'reversed': bool(flags & 0x01),
        'oneShot': bool(flags & 0x02)
    }


def parse_set_color_data(buffer: bytes, offset: int = 0) -> dict:
    """
    Parse SetColorData from a buffer.

    Layout (5 bytes total):
        - zoneId: uint16_t
        - color: AnimationColor (3 bytes)
    """
    if len(buffer) < offset + SET_COLOR_DATA_SIZE:
        raise ValueError(
            f"Buffer too small for SetColorData at offset {offset}")

    zone_id, = struct.unpack('<H', buffer[offset:offset + 2])
    color = parse_animation_color(buffer, offset + 2)

    return {
        'zoneId': zone_id,
        'color': color
    }


def parse_set_animation_sequence_data(buffer: bytes, offset: int = 0) -> dict:
    """
    Parse SetAnimationSequenceData from a buffer.

    Layout (4 bytes total):
        - zoneId: uint16_t
        - sequenceId: uint16_t
    """
    if len(buffer) < offset + SET_ANIMATION_SEQUENCE_DATA_SIZE:
        raise ValueError(
            f"Buffer too small for SetAnimationSequenceData at offset {offset}")

    zone_id, sequence_id = struct.unpack('<HH', buffer[offset:offset + 4])

    return {
        'zoneId': zone_id,
        'sequenceId': sequence_id
    }


def parse_transmission_header(buffer: bytes) -> dict:
    """
    Parse a TransmissionHeader from the start of a buffer.

    Layout (8 bytes total):
        - type: uint8_t (TransmissionType)
        - dataLength: uint32_t
        - packetCount: uint16_t
        - flags: uint8_t (bit 0 = compressed)
    """
    if len(buffer) < TRANSMISSION_HEADER_SIZE:
        raise ValueError(
            f"Buffer too small for TransmissionHeader: {len(buffer)} < {TRANSMISSION_HEADER_SIZE}")

    trans_type, data_length, packet_count, flags = struct.unpack(
        '<BIHB', buffer[:TRANSMISSION_HEADER_SIZE])
    return {
        'type': trans_type,
        'dataLength': data_length,
        'packetCount': packet_count,
        'compressed': bool(flags & 0x01),
        'raw': buffer[:TRANSMISSION_HEADER_SIZE]
    }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sdk():
    """Provide the lumyn_sdk module."""
    import lumyn_sdk
    return lumyn_sdk


@pytest.fixture
def command_builder(sdk):
    """Provide the CommandBuilder class."""
    return sdk._command.CommandBuilder


@pytest.fixture
def id_creator(sdk):
    """Provide the IDCreator class for hashing zone/animation names."""
    return sdk._util.hashing.IDCreator


@pytest.fixture
def animation_color_factory(sdk):
    """Factory to create AnimationColor instances."""
    def create(r: int = 0, g: int = 0, b: int = 0):
        color = sdk._command.AnimationColor()
        color.r = r
        color.g = g
        color.b = b
        return color
    return create


@pytest.fixture
def mock_led_handler():
    """Provide a real LedHandler from ConnectorX without connecting to serial."""
    import lumyn_sdk as sdk

    # Create a real ConnectorX device without connecting
    # This allows real builders to be created and tested without serial I/O
    device = sdk.ConnectorX()

    return device.leds
