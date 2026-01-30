"""
Type stubs for lumyn_sdk package

This provides type information for the C++ bindings exposed by the lumyn_sdk package.
"""

from . import interfaces as interfaces
from . import domain as domain
from . import devices as devices
from .enums import (
    EventType as EventType,
    Status as Status,
    EventDisabledCause as EventDisabledCause,
    EventErrorType as EventErrorType,
    EventFatalErrorType as EventFatalErrorType,
    EventConnectionType as EventConnectionType,
    ZoneType as ZoneType,
    NetworkType as NetworkType,
    Animation as Animation,
    MatrixTextScrollDirection as MatrixTextScrollDirection,
    MatrixTextFont as MatrixTextFont,
    MatrixTextAlign as MatrixTextAlign,
)
from .command import MatrixTextFlags as MatrixTextFlags
from .interfaces.i_event_callback import IEventCallback as IEventCallback
from .interfaces.i_module_data_callback import IModuleDataCallback as IModuleDataCallback
from .domain.module.module_handler import ModuleHandler as ModuleHandler
from .domain.led.led_handler import LedHandler as LedHandler
from .domain.led.direct_led import DirectLED as DirectLED
from .domain.event.event import Event as Event
from .domain.module.new_data_info import NewDataInfo as NewDataInfo
from .devices.connectorx import ConnectorX as ConnectorX
from .devices.connectorx_animate import ConnectorXAnimate as ConnectorXAnimate
from typing import Optional, List, Callable, Dict, Any, Union, Tuple
from types import ModuleType

# Version info
__version__: str
DRIVER_VERSION_MAJOR: int
DRIVER_VERSION_MINOR: int
DRIVER_VERSION_PATCH: int

# Device imports

# Enums

# Submodule packages

# C++ binding submodules - these are loaded dynamically at runtime
# Stub classes for the command submodule


class _CommandModule:
    """Type stub for lumyn_sdk.command C++ module."""

    class CommandType:
        System: int
        LED: int
        Device: int

    class LEDCommandType:
        SetAnimation: int
        SetAnimationGroup: int
        SetColor: int
        SetColorGroup: int
        SetAnimationSequence: int
        SetAnimationSequenceGroup: int
        SetBitmap: int
        SetBitmapGroup: int
        SetMatrixText: int
        SetMatrixTextGroup: int
        SetDirectBuffer: int

    class SystemCommandType:
        ClearStatusFlag: int
        SetAssignedId: int
        RestartDevice: int

    class MatrixTextScrollDirection:
        LEFT: int
        RIGHT: int

    class MatrixTextFont:
        BUILTIN: int
        TINY_3X3: int
        PICOPIXEL: int
        TOM_THUMB: int
        ORG_01: int
        FREE_MONO_9: int
        FREE_MONO_BOLD_9: int
        FREE_SANS_9: int
        FREE_SANS_BOLD_9: int
        FREE_SERIF_9: int
        FREE_SERIF_BOLD_9: int
        FREE_MONO_12: int
        FREE_MONO_BOLD_12: int
        FREE_SANS_12: int
        FREE_SANS_BOLD_12: int
        FREE_SERIF_12: int
        FREE_SERIF_BOLD_12: int
        FREE_MONO_18: int
        FREE_MONO_BOLD_18: int
        FREE_SANS_18: int
        FREE_SANS_BOLD_18: int
        FREE_SERIF_18: int
        FREE_SERIF_BOLD_18: int
        FREE_MONO_24: int
        FREE_MONO_BOLD_24: int
        FREE_SANS_24: int
        FREE_SANS_BOLD_24: int
        FREE_SERIF_24: int
        FREE_SERIF_BOLD_24: int

    class MatrixTextAlign:
        LEFT: int
        CENTER: int
        RIGHT: int

    class MatrixTextFlags:
        smoothScroll: bool
        showBackground: bool
        pingPong: bool
        noScroll: bool
        reserved: int
        def __init__(self) -> None: ...

    class AnimationColor:
        r: int
        g: int
        b: int
        def __init__(self, r: int = 0, g: int = 0, b: int = 0) -> None: ...

    class SetAnimationData:
        zoneId: int
        animationId: int
        delay: int
        color: 'AnimationColor'
        reversed: bool
        oneShot: bool
        def __init__(self) -> None: ...

    class SetColorData:
        zoneId: int
        color: 'AnimationColor'
        def __init__(self) -> None: ...

    class CommandBuilder:
        @staticmethod
        def build(header: Any, body: bytes = b"") -> bytes: ...

        @staticmethod
        def buildSetAnimation(zone_id: int, animation_id: int, color: 'AnimationColor',
                              delay: int = 250, reversed: bool = False, one_shot: bool = False) -> bytes: ...

        @staticmethod
        def buildSetAnimationGroup(group_id: int, animation_id: int, color: 'AnimationColor',
                                   delay: int = 250, reversed: bool = False, one_shot: bool = False) -> bytes: ...

        @staticmethod
        def buildSetColor(zone_id: int, color: 'AnimationColor') -> bytes: ...

        @staticmethod
        def buildSetColorGroup(
            group_id: int, color: 'AnimationColor') -> bytes: ...

        @staticmethod
        def buildSetAnimationSequence(
            zone_id: int, sequence_id: int) -> bytes: ...

        @staticmethod
        def buildSetAnimationSequenceGroup(
            group_id: int, sequence_id: int) -> bytes: ...

        @staticmethod
        def buildSetBitmap(zone_id: int, bitmap_id: int, color: 'AnimationColor',
                           set_color: bool = False, one_shot: bool = False) -> bytes: ...

        @staticmethod
        def buildSetBitmapGroup(group_id: int, bitmap_id: int, color: 'AnimationColor',
                                set_color: bool = False, one_shot: bool = False) -> bytes: ...

        @staticmethod
        def buildSetMatrixText(zone_id: int, text: str, color: 'AnimationColor',
                               direction: int = 0, delay: int = 500, one_shot: bool = False,
                               bg_color: 'AnimationColor' = AnimationColor(), font: int = 0,
                               align: int = 0, flags: 'MatrixTextFlags' = MatrixTextFlags(),
                               y_offset: int = 0) -> bytes: ...

        @staticmethod
        def buildSetMatrixTextGroup(group_id: int, text: str, color: 'AnimationColor',
                                    direction: int = 0, delay: int = 500, one_shot: bool = False,
                                    bg_color: 'AnimationColor' = AnimationColor(), font: int = 0,
                                    align: int = 0, flags: 'MatrixTextFlags' = MatrixTextFlags(),
                                    y_offset: int = 0) -> bytes: ...


class _ConnectorXModule:
    """Type stub for lumyn_sdk.connectorx C++ module."""

    class Animation:
        None_: int
        Fill: int
        Blink: int
        Breathe: int
        RainbowRoll: int
        SineRoll: int
        Chase: int
        FadeIn: int
        FadeOut: int
        RainbowCycle: int
        AlternateBreathe: int
        GrowingBreathe: int
        Comet: int
        Sparkle: int
        Fire: int
        Scanner: int
        TheaterChase: int
        Twinkle: int
        Meteor: int
        Wave: int
        Pulse: int
        Larson: int
        Ripple: int
        Confetti: int
        Lava: int
        Plasma: int
        Heartbeat: int

    class LEDCommander:
        def SetColor(self, zone_id: str,
                     color: '_CommandModule.AnimationColor') -> None: ...

        def SetGroupColor(self, group_id: str,
                          color: '_CommandModule.AnimationColor') -> None: ...

        def SetAnimation(self, zone_id: str, animation: 'Animation', color: '_CommandModule.AnimationColor',
                         delay_ms: int = 250, reversed: bool = False, one_shot: bool = False) -> None: ...

        def SetGroupAnimation(self, group_id: str, animation: 'Animation', color: '_CommandModule.AnimationColor',
                              delay_ms: int = 250, reversed: bool = False, one_shot: bool = False) -> None: ...

        def SetAnimationSequence(
            self, zone_id: str, sequence_id: str) -> None: ...
        def SetGroupAnimationSequence(
            self, group_id: str, sequence_id: str) -> None: ...

    class MatrixCommander:
        def SetText(self, zone_id: str, text: str, color: '_CommandModule.AnimationColor',
                    direction: int = 0, delay_ms: int = 500, one_shot: bool = False,
                    bg_color: '_CommandModule.AnimationColor' = _CommandModule.AnimationColor(),
                    font: int = 0, align: int = 0,
                    flags: '_CommandModule.MatrixTextFlags' = _CommandModule.MatrixTextFlags(),
                    y_offset: int = 0) -> None: ...

        def SetGroupText(self, group_id: str, text: str, color: '_CommandModule.AnimationColor',
                         direction: int = 0, delay_ms: int = 500, one_shot: bool = False,
                         bg_color: '_CommandModule.AnimationColor' = _CommandModule.AnimationColor(),
                         font: int = 0, align: int = 0,
                         flags: '_CommandModule.MatrixTextFlags' = _CommandModule.MatrixTextFlags(),
                         y_offset: int = 0) -> None: ...

        def SetBitmap(self, zone_id: str, sequence_id: str, color: '_CommandModule.AnimationColor',
                      set_color: bool = False, one_shot: bool = False) -> None: ...
        def SetGroupBitmap(self, group_id: str, sequence_id: str, color: '_CommandModule.AnimationColor',
                           set_color: bool = False, one_shot: bool = False) -> None: ...

    class ConnectorXInternal:
        def __init__(self) -> None: ...
        def GetEvents(self) -> List[Any]: ...
        def leds(self) -> '_ConnectorXModule.LEDCommander': ...
        def matrix(self) -> '_ConnectorXModule.MatrixCommander': ...
        def GetLatestModuleData(
            self, module_id: str) -> List[Dict[str, Any]]: ...

        def RequestConfig(self, timeout_ms: int = 5000) -> Optional[str]: ...


class _EventModule:
    """Type stub for lumyn_sdk.event C++ module."""

    class EventType:
        BeginInitialization: int
        FinishInitialization: int
        Enabled: int
        Disabled: int
        Connected: int
        Disconnected: int
        Error: int
        FatalError: int
        RegisteredEntity: int
        Custom: int
        PinInterrupt: int
        HeartBeat: int

    class Status:
        Unknown: int
        Booting: int
        Active: int
        Error: int
        Fatal: int

    class DisabledCause:
        NoHeartbeat: int
        Manual: int
        EStop: int
        Restart: int

    class ConnectionType:
        USB: int
        WebUSB: int
        I2C: int
        CAN: int
        UART: int

    class ErrorType:
        FileNotFound: int
        InvalidFile: int
        EntityNotFound: int
        DeviceMalfunction: int
        QueueFull: int
        LedStrip: int
        LedMatrix: int
        InvalidAnimationSequence: int
        InvalidChannel: int
        DuplicateID: int
        InvalidConfigUpload: int
        ModuleError: int

    class Event:
        type: 'EventType'
        data: Any
        def __init__(self) -> None: ...


class _UtilModule:
    """Type stub for lumyn_sdk.util C++ module."""

    class CircularBuffer:
        def __init__(self, capacity: int) -> None: ...
        def push(self, data: bytes) -> None: ...
        def pop(self) -> int: ...
        def front(self) -> int: ...
        def size(self) -> int: ...
        def capacity(self) -> int: ...

    class hashing:
        class MD5:
            @staticmethod
            def hash(data: bytes) -> bytes: ...

        class IDCreator:
            @staticmethod
            def createId(input: str) -> int: ...


# Module-level C++ binding references
cpp_bindings: Optional[Any]
connectorx: Optional[_ConnectorXModule]
command: Optional[_CommandModule]
event: Optional[_EventModule]
file: Optional[Any]
# Internal C++ bindings, use LedHandler.create_direct_led() instead
led: Optional[Any]
module: Optional[Any]
packet: Optional[Any]
request: Optional[Any]
response: Optional[Any]
transmission: Optional[Any]
serial: Optional[Any]
util: Optional[_UtilModule]

# Convenience function to create ID from string


def createId(input: str) -> int:
    """Create a 16-bit ID from a string using the IDCreator."""
    ...


def list_available_ports() -> List[str]:
    """
    List available serial ports that could be ConnectorX devices.

    Returns:
        List of port names (e.g., ["COM3", "COM4"] on Windows or ["/dev/ttyUSB0"] on Linux)
    """
    ...


def SerializeConfigToJson(config: Any) -> str:
    """
    Serialize configuration to JSON string.

    Args:
        config: Configuration dict or object

    Returns:
        JSON string representation
    """
    ...
