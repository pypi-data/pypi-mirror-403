"""
Enumeration definitions for the Lumyn SDK

This module contains all the enums used throughout the SDK.
Most enums are FALLBACK definitions - the C++ SDK bindings provide the authoritative
versions which should be used at runtime. These Python definitions are only for:
- Build-time type hints
- When bindings are unavailable
- IDE autocomplete support

See lumyn_sdk/src/bindings/*.cpp for the C++ bound versions.
"""

from enum import Enum, IntEnum


class EventType(IntEnum):
    """Event type enumeration - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.EventType.
    This Python definition matches the Java vendordep and C++ SDK.
    Values are bitmask flags for event filtering.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    BeginInitialization = 0
    FinishInitialization = 1
    Enabled = 2
    Disabled = 4
    Connected = 8
    Disconnected = 16
    Error = 32
    FatalError = 64
    RegisteredEntity = 128
    Custom = 256
    PinInterrupt = 512
    HeartBeat = 1024


class Animation(IntEnum):
    """LED Animation types - FALLBACK definition for when C++ bindings unavailable.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.Animation.
    This Python definition is only used as a fallback during build or when
    bindings are not available. The C++ bound version should be preferred
    to avoid duplicating common's enum definitions.

    See: lumyn_sdk/src/bindings/connectorx_bindings.cpp
    """
    None_ = 0
    Fill = 1
    Blink = 2
    Breathe = 3
    RainbowRoll = 4
    SineRoll = 5
    Chase = 6
    FadeIn = 7
    FadeOut = 8
    RainbowCycle = 9
    AlternateBreathe = 10
    GrowingBreathe = 11
    Comet = 12
    Sparkle = 13
    Fire = 14
    Scanner = 15
    TheaterChase = 16
    Twinkle = 17
    Meteor = 18
    Wave = 19
    Pulse = 20
    Larson = 21
    Ripple = 22
    Confetti = 23
    Lava = 24
    Plasma = 25
    Heartbeat = 26


class Status(IntEnum):
    """Device status enumeration - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.Status.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    Unknown = -1
    Booting = 0
    Active = 1
    Error = 2
    Fatal = 3


# Alias for backward compatibility
DeviceStatus = Status


class EventConnectionType(IntEnum):
    """Connection type enumeration for events - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.ConnectionType.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    USB = 0
    WEB_USB = 1
    I2C = 2
    CAN = 3
    UART = 4


class EventDisabledCause(IntEnum):
    """Event disabled cause enumeration - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.DisabledCause.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    NoHeartbeat = 0
    Manual = 1
    EStop = 2
    Restart = 3


class EventErrorType(IntEnum):
    """Event error type enumeration - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.ErrorType.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    FileNotFound = 0
    InvalidFile = 1
    EntityNotFound = 2
    DeviceMalfunction = 3
    QueueFull = 4
    LedStrip = 5
    LedMatrix = 6
    InvalidAnimationSequence = 7
    InvalidChannel = 8
    DuplicateID = 9
    InvalidConfigUpload = 10
    ModuleError = 11


class EventFatalErrorType(IntEnum):
    """Event fatal error type enumeration - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk._bindings.event.FatalErrorType.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    InitError = 0
    BadConfig = 1
    StartTask = 2
    CreateQueue = 3


class MatrixTextScrollDirection(IntEnum):
    """Matrix text scroll directions - FALLBACK definition for when C++ bindings unavailable.

    NOTE: This enum is bound from C++ in lumyn_sdk.command.MatrixTextScrollDirection.
    This Python definition is only used as a fallback during build or when
    bindings are not available. The C++ bound version should be preferred
    to avoid duplicating common's enum definitions.

    See: lumyn_sdk/src/bindings/command_bindings.cpp
    """
    LEFT = 0
    RIGHT = 1


class MatrixTextFont(IntEnum):
    """Matrix text fonts - FALLBACK definition for when C++ bindings unavailable.

    NOTE: This enum is bound from C++ in lumyn_sdk.command.MatrixTextFont.
    This Python definition is only used as a fallback during build or when
    bindings are not available. The C++ bound version should be preferred
    to avoid duplicating common's enum definitions.
    """
    BUILTIN = 0
    TINY_3X3 = 1
    PICOPIXEL = 2
    TOM_THUMB = 3
    ORG_01 = 4
    FREE_MONO_9 = 10
    FREE_MONO_BOLD_9 = 11
    FREE_SANS_9 = 12
    FREE_SANS_BOLD_9 = 13
    FREE_SERIF_9 = 14
    FREE_SERIF_BOLD_9 = 15
    FREE_MONO_12 = 20
    FREE_MONO_BOLD_12 = 21
    FREE_SANS_12 = 22
    FREE_SANS_BOLD_12 = 23
    FREE_SERIF_12 = 24
    FREE_SERIF_BOLD_12 = 25
    FREE_MONO_18 = 30
    FREE_MONO_BOLD_18 = 31
    FREE_SANS_18 = 32
    FREE_SANS_BOLD_18 = 33
    FREE_SERIF_18 = 34
    FREE_SERIF_BOLD_18 = 35
    FREE_MONO_24 = 40
    FREE_MONO_BOLD_24 = 41
    FREE_SANS_24 = 42
    FREE_SANS_BOLD_24 = 43
    FREE_SERIF_24 = 44
    FREE_SERIF_BOLD_24 = 45


class MatrixTextAlign(IntEnum):
    """Matrix text alignment when noScroll is enabled - FALLBACK for C++ bindings.

    NOTE: This enum is bound from C++ in lumyn_sdk.command.MatrixTextAlign.
    This Python definition matches the Java vendordep and C++ SDK.

    See: lumyn_sdk/src/bindings/command_bindings.cpp
    """
    Left = 0
    Center = 1
    Right = 2


class ZoneType(Enum):
    """Zone type enumeration from Java vendordep.

    Defines whether a zone is a LED strip or LED matrix.
    """
    Strip = "Strip"
    Matrix = "Matrix"


class NetworkType(Enum):
    """Network type enumeration from Java vendordep.

    Defines the communication network type for device connections.
    """
    I2C = "I2C"
    USB = "USB"
    CAN = "CAN"
    UART = "UART"


class EventConnectionType(IntEnum):
    """Event connection type enumeration - FALLBACK definition for when C++ bindings unavailable.

    NOTE: This enum should match lumyn::internal::Eventing::ConnectionType from C++ bindings.
    The C++ bound version is available at lumyn_sdk._bindings.event.ConnectionType.
    This Python definition is only used as a fallback during build or when bindings are not available.

    See: lumyn_sdk/src/bindings/event_bindings.cpp
    """
    USB = 0
    WEB_USB = 1
    I2C = 2
    CAN = 3
    UART = 4
