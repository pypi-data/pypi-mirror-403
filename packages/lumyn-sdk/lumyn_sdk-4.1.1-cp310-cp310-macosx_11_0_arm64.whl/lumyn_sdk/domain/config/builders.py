"""
Fluent builder API for creating device configurations.

Provides nested builders matching the Java vendordep API exactly.
"""

from typing import Optional, List, Dict, Any
from .models import (
    DeviceConfig,
    Network,
    Channel,
    Zone,
    AnimationColor,
    AnimationStep,
    AnimationSequence,
    Bitmap,
    Module,
    AnimationGroup,
)
from .enums import NetworkType, ZoneType, BitmapType


class ConfigBuilder:
    """Root configuration builder"""

    def __init__(self):
        self._team_number: Optional[str] = None
        self._network_type = NetworkType.USB
        self._network_address: Optional[int] = None
        self._baud_rate: Optional[int] = None
        self._md5: Optional[bytes] = None
        self._channels: List[Channel] = []
        self._sequences: List[AnimationSequence] = []
        self._bitmaps: List[Bitmap] = []
        self._modules: List[Module] = []
        self._groups: List[AnimationGroup] = []

    def for_team(self, team_number: str) -> "ConfigBuilder":
        """Set team number"""
        self._team_number = team_number
        return self

    def set_network_type(self, network_type: NetworkType) -> "ConfigBuilder":
        """Set network type"""
        if network_type is not None:
            self._network_type = network_type
        return self

    def set_baud_rate(self, baud: int) -> "ConfigBuilder":
        """Set UART baud rate (validates allowed values)"""
        allowed = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        if baud in allowed:
            self._baud_rate = baud
        else:
            self._baud_rate = 115200
        return self

    def set_i2c_address(self, address: int) -> "ConfigBuilder":
        """Set I2C address (0-255)"""
        self._network_address = max(0, min(255, address))
        return self

    def with_md5(self, md5_bytes: bytes) -> "ConfigBuilder":
        """Set MD5 hash (16 bytes)"""
        if md5_bytes and len(md5_bytes) == 16:
            self._md5 = md5_bytes
        return self

    def add_channel(self, channel_num: int, channel_id: str, length: int) -> "ChannelBuilder":
        """Add a channel (returns ChannelBuilder)"""
        return ChannelBuilder(self, channel_num, channel_id, length)

    def add_sequence(self, sequence_id: str) -> "SequenceBuilder":
        """Add animation sequence (returns SequenceBuilder)"""
        return SequenceBuilder(self, sequence_id)

    def add_bitmap(self, bitmap_id: str) -> "BitmapBuilder":
        """Add bitmap/image (returns BitmapBuilder)"""
        return BitmapBuilder(self, bitmap_id)

    def add_module(self, module_id: str, module_type: str,
                   polling_rate_ms: int, connection_type: str) -> "ModuleBuilder":
        """Add sensor/module (returns ModuleBuilder)"""
        return ModuleBuilder(self, module_id, module_type, polling_rate_ms, connection_type)

    def add_group(self, group_id: str) -> "GroupBuilder":
        """Add zone group (returns GroupBuilder)"""
        return GroupBuilder(self, group_id)

    def build(self) -> DeviceConfig:
        """Build the final DeviceConfig"""
        return DeviceConfig(
            network=Network(self._network_type, self._network_address, self._baud_rate),
            channels=self._channels.copy(),
            md5=self._md5,
            team_number=self._team_number,
            sequences=self._sequences.copy(),
            bitmaps=self._bitmaps.copy(),
            modules=self._modules.copy(),
            groups=self._groups.copy()
        )

    # Package-private methods for nested builders
    def _add_built_channel(self, channel: Channel) -> None:
        """Add a built channel (called by ChannelBuilder)"""
        self._channels.append(channel)

    def _add_built_sequence(self, sequence: AnimationSequence) -> None:
        """Add a built sequence (called by SequenceBuilder)"""
        self._sequences.append(sequence)

    def _add_built_bitmap(self, bitmap: Bitmap) -> None:
        """Add a built bitmap (called by BitmapBuilder)"""
        self._bitmaps.append(bitmap)

    def _add_built_module(self, module: Module) -> None:
        """Add a built module (called by ModuleBuilder)"""
        self._modules.append(module)

    def _add_built_group(self, group: AnimationGroup) -> None:
        """Add a built group (called by GroupBuilder)"""
        self._groups.append(group)


class ChannelBuilder:
    """Builder for LED channel configuration"""

    def __init__(self, root: ConfigBuilder, channel_num: int, channel_id: str, length: int):
        self._root = root
        self._key = str(channel_num)
        self._id = channel_id
        self._length = length
        self._brightness: Optional[int] = None
        self._zones: List[Zone] = []

    def brightness(self, brightness: int) -> "ChannelBuilder":
        """Set channel brightness (0-255)"""
        self._brightness = max(0, min(255, brightness))
        return self

    def add_strip_zone(self, zone_id: str, length: int,
                       reversed: bool = False, brightness: Optional[int] = None) -> "ChannelBuilder":
        """Add a strip zone"""
        clamped_brightness = None
        if brightness is not None:
            clamped_brightness = max(0, min(255, brightness))

        self._zones.append(Zone(
            type=ZoneType.STRIP,
            id=zone_id,
            brightness=clamped_brightness,
            strip_length=length,
            reversed=reversed
        ))
        return self

    def add_matrix_zone(self, zone_id: str, rows: int, cols: int,
                        brightness: Optional[int] = None, orientation: Optional[Dict[str, Any]] = None) -> "ChannelBuilder":
        """Add a matrix zone"""
        clamped_brightness = None
        if brightness is not None:
            clamped_brightness = max(0, min(255, brightness))

        self._zones.append(Zone(
            type=ZoneType.MATRIX,
            id=zone_id,
            brightness=clamped_brightness,
            matrix_rows=rows,
            matrix_cols=cols,
            matrix_orientation=orientation
        ))
        return self

    def end_channel(self) -> ConfigBuilder:
        """Complete this channel and return to root builder"""
        self._root._add_built_channel(Channel(
            key=self._key,
            id=self._id,
            length=self._length,
            brightness=self._brightness,
            zones=self._zones.copy()
        ))
        return self._root


class StepBuilder:
    """Builder for animation sequence step"""

    def __init__(self, parent: "SequenceBuilder", animation_id: str):
        self._parent = parent
        self._animation_id = animation_id
        self._color: Optional[AnimationColor] = None
        self._delay: int = 100
        self._reversed: bool = False
        self._repeat: Optional[int] = None

    def with_color(self, r: int, g: int, b: int) -> "StepBuilder":
        """Set animation color"""
        self._color = AnimationColor(
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b))
        )
        return self

    def with_delay(self, delay_ms: int) -> "StepBuilder":
        """Set frame delay"""
        self._delay = max(0, delay_ms)
        return self

    def reverse(self, reversed: bool = True) -> "StepBuilder":
        """Set animation direction"""
        self._reversed = reversed
        return self

    def with_repeat(self, count: int) -> "StepBuilder":
        """Set repeat count (0 = infinite)"""
        self._repeat = max(0, count)
        return self

    def end_step(self) -> "SequenceBuilder":
        """Complete this step and return to sequence builder"""
        self._parent._add_built_step(AnimationStep(
            animation_id=self._animation_id,
            color=self._color,
            delay=self._delay,
            reversed=self._reversed,
            repeat=self._repeat
        ))
        return self._parent


class SequenceBuilder:
    """Builder for animation sequence"""

    def __init__(self, root: ConfigBuilder, sequence_id: str):
        self._root = root
        self._id = sequence_id
        self._steps: List[AnimationStep] = []

    def add_step(self, animation_id: str) -> StepBuilder:
        """Add a step to this sequence"""
        return StepBuilder(self, animation_id)

    def _add_built_step(self, step: AnimationStep) -> None:
        """Add a built step (called by StepBuilder)"""
        self._steps.append(step)

    def end_sequence(self) -> ConfigBuilder:
        """Complete this sequence and return to root builder"""
        self._root._add_built_sequence(AnimationSequence(
            id=self._id,
            steps=self._steps.copy()
        ))
        return self._root


class BitmapBuilder:
    """Builder for bitmap/image configuration"""

    def __init__(self, root: ConfigBuilder, bitmap_id: str):
        self._root = root
        self._id = bitmap_id
        self._type: Optional[BitmapType] = None
        self._path: Optional[str] = None
        self._folder: Optional[str] = None
        self._frame_delay: Optional[int] = None

    def static(self, path: str) -> "BitmapBuilder":
        """Set this as a static bitmap"""
        self._type = BitmapType.STATIC
        self._path = path
        self._folder = None
        self._frame_delay = None
        return self

    def animated(self, folder: str, frame_delay_ms: int) -> "BitmapBuilder":
        """Set this as an animated bitmap sequence"""
        self._type = BitmapType.ANIMATED
        self._folder = folder
        self._frame_delay = max(0, frame_delay_ms)
        self._path = None
        return self

    def end_bitmap(self) -> ConfigBuilder:
        """Complete this bitmap and return to root builder"""
        if self._type is None:
            raise ValueError("Bitmap type must be set (call static() or animated())")
        self._root._add_built_bitmap(Bitmap(
            id=self._id,
            type=self._type,
            path=self._path,
            folder=self._folder,
            frame_delay=self._frame_delay
        ))
        return self._root


class ModuleBuilder:
    """Builder for sensor/module configuration"""

    def __init__(self, root: ConfigBuilder, module_id: str, module_type: str,
                 polling_rate_ms: int, connection_type: str):
        self._root = root
        self._id = module_id
        self._type = module_type
        self._polling_rate_ms = max(0, polling_rate_ms)
        self._connection_type = connection_type
        self._config: Dict[str, Any] = {}

    def with_config(self, key: str, value: Any) -> "ModuleBuilder":
        """Add a configuration key-value pair for this module"""
        self._config[key] = value
        return self

    def end_module(self) -> ConfigBuilder:
        """Complete this module and return to root builder"""
        self._root._add_built_module(Module(
            id=self._id,
            type=self._type,
            polling_rate_ms=self._polling_rate_ms,
            connection_type=self._connection_type,
            config=self._config.copy() if self._config else None
        ))
        return self._root


class GroupBuilder:
    """Builder for zone group configuration"""

    def __init__(self, root: ConfigBuilder, group_id: str):
        self._root = root
        self._id = group_id
        self._zone_ids: List[str] = []

    def add_zone(self, zone_id: str) -> "GroupBuilder":
        """Add a zone ID to this group"""
        self._zone_ids.append(zone_id)
        return self

    def end_group(self) -> ConfigBuilder:
        """Complete this group and return to root builder"""
        self._root._add_built_group(AnimationGroup(
            id=self._id,
            zone_ids=self._zone_ids.copy()
        ))
        return self._root
