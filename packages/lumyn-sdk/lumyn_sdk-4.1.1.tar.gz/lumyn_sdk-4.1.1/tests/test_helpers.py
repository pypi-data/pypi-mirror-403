"""
Helper functions and constants for Lumyn SDK tests.

Provides parsing utilities and struct size constants for verifying
command serialization matches firmware expectations.
"""

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


class AnimationId:
    """Animation enum values - matches lumyn::led::Animation from C++"""
    NONE = 0
    FILL = 1
    BLINK = 2
    BREATHE = 3
    RAINBOW_ROLL = 4
    SINE_ROLL = 5
    CHASE = 6
    FADE_IN = 7
    FADE_OUT = 8
    RAINBOW_CYCLE = 9
    ALTERNATE_BREATHE = 10
    GROWING_BREATHE = 11
    COMET = 12
    SPARKLE = 13
    FIRE = 14
    SCANNER = 15
    THEATER_CHASE = 16
    TWINKLE = 17
    METEOR = 18
    WAVE = 19
    PULSE = 20
    LARSON = 21
    RIPPLE = 22
    CONFETTI = 23
    LAVA = 24
    PLASMA = 25
    HEARTBEAT = 26


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
