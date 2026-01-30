from __future__ import annotations

import struct
from dataclasses import dataclass

from ..domain.module.module_base import ModuleBase
from ..domain.module.new_data_info import NewDataInfo


@dataclass
class VL53L1XPayload:
    """Parsed VL53L1X distance payload."""

    valid: int = 0
    dist: int = 0  # millimeters


class VL53L1XModule(ModuleBase[VL53L1XPayload]):
    """Typed helper for VL53L1X time-of-flight modules."""

    def __init__(self, device: "ConnectorX", module_id: str):
        super().__init__(device, module_id)

    def parse(self, entry: NewDataInfo) -> VL53L1XPayload:
        payload = VL53L1XPayload()
        if entry.data and entry.len >= 3:
            payload.valid = entry.data[0]
            payload.dist = struct.unpack("<H", entry.data[1:3])[0]
        return payload
