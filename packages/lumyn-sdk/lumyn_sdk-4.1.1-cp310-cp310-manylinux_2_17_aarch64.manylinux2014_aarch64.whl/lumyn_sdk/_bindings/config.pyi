"""
Type stubs for lumyn_sdk._bindings.config
"""

from typing import Optional, List
from enum import IntEnum


class NetworkType(IntEnum):
    USB = 0
    CAN = 1
    I2C = 2
    UART = 3


class ZoneType(IntEnum):
    STRIP = 0
    MATRIX = 1


class BitmapType(IntEnum):
    STATIC = 0
    ANIMATED = 1


class Color:
    r: int
    g: int
    b: int
    def __init__(self, r: int = 0, g: int = 0, b: int = 0) -> None: ...


class NetworkConfig:
    mode: NetworkType


class MatrixOrientation:
    corner_top_bottom: str
    corner_left_right: str
    axis_layout: str
    sequence_layout: str


class Zone:
    id: str
    brightness: int
    type: str
    length: int
    reversed: bool
    # Matrix-specific
    rows: int
    cols: int
    orientation: Optional[MatrixOrientation]


class ChannelConfig:
    id: str
    length: int
    brightness: int
    zones: List[Zone]


class SequenceStep:
    animation_id: str
    color: Optional[Color]
    delay: int
    reversed: bool
    repeat: int


class Sequence:
    id: str
    steps: List[SequenceStep]


class Bitmap:
    id: str
    type: BitmapType
    folder: Optional[str]


class Module:
    id: str
    connection_type: str


class AnimationGroup:
    id: str
    zones: List[str]


class LumynConfiguration:
    """Parsed device configuration."""
    team_number: Optional[int]
    network: Optional[NetworkConfig]
    channels: Optional[List[ChannelConfig]]
    sequences: Optional[List[Sequence]]
    bitmaps: Optional[List[Bitmap]]
    sensors: Optional[List[Module]]
    modules: Optional[List[Module]]
    animation_groups: Optional[List[AnimationGroup]]
    groups: Optional[List[AnimationGroup]]


class ConfigBuilder:
    def __init__(self) -> None: ...
    def set_network_mode(self, mode: NetworkType) -> "ConfigBuilder": ...
    def add_channel(self, channel_id: str, length: int,
                    brightness: int = 255) -> "ConfigBuilder": ...

    def build_json(self) -> str: ...


def ParseConfig(json_string: str) -> Optional[LumynConfiguration]:
    """Parse a JSON configuration string into a LumynConfiguration object."""
    ...


def SerializeConfigToJson(config: LumynConfiguration) -> str:
    """Serialize a LumynConfiguration object to JSON string."""
    ...
