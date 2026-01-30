"""
Configuration data models (dataclasses).

These classes represent the structure of device configurations,
matching the Java vendordep LumynDeviceConfig structure.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .enums import NetworkType, ZoneType, BitmapType


@dataclass
class Network:
    """Network configuration"""
    type: NetworkType
    address: Optional[int] = None
    baud_rate: Optional[int] = None


@dataclass
class Zone:
    """LED zone configuration"""
    type: ZoneType
    id: str
    brightness: Optional[int] = None
    strip_length: int = 0
    reversed: bool = False
    matrix_rows: int = 0
    matrix_cols: int = 0
    matrix_orientation: Optional[Dict[str, Any]] = None


@dataclass
class Channel:
    """LED channel configuration"""
    key: str
    id: str
    length: int
    brightness: Optional[int] = None
    zones: List[Zone] = field(default_factory=list)


@dataclass
class AnimationColor:
    """RGB color for animations"""
    r: int
    g: int
    b: int


@dataclass
class AnimationStep:
    """Animation sequence step"""
    animation_id: str
    color: Optional[AnimationColor] = None
    delay: int = 100
    reversed: bool = False
    repeat: Optional[int] = None


@dataclass
class AnimationSequence:
    """Animation sequence"""
    id: str
    steps: List[AnimationStep] = field(default_factory=list)


@dataclass
class Bitmap:
    """Bitmap/image configuration"""
    id: str
    type: BitmapType
    path: Optional[str] = None
    folder: Optional[str] = None
    frame_delay: Optional[int] = None


@dataclass
class Module:
    """Sensor/module configuration"""
    id: str
    type: str
    polling_rate_ms: int
    connection_type: str
    config: Optional[Dict[str, Any]] = None


@dataclass
class AnimationGroup:
    """Zone group configuration"""
    id: str
    zone_ids: List[str] = field(default_factory=list)


@dataclass
class DeviceConfig:
    """Complete device configuration"""
    network: Network
    channels: List[Channel] = field(default_factory=list)
    md5: Optional[bytes] = None
    team_number: Optional[str] = None
    sequences: List[AnimationSequence] = field(default_factory=list)
    bitmaps: List[Bitmap] = field(default_factory=list)
    modules: List[Module] = field(default_factory=list)
    groups: List[AnimationGroup] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string"""
        from .serialization import ConfigSerializer
        return ConfigSerializer.to_json(self)

    @staticmethod
    def from_json(json_str: str) -> "DeviceConfig":
        """Deserialize from JSON string"""
        from .serialization import ConfigSerializer
        return ConfigSerializer.from_json(json_str)
