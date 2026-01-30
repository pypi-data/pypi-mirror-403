from __future__ import annotations

from dataclasses import dataclass

from ..domain.module.module_base import ModuleBase
from ..domain.module.new_data_info import NewDataInfo


@dataclass
class AnalogInputPayload:
    """Parsed analog input payload."""

    raw_value: int = 0
    scaled_value: int = 0


class AnalogInputModule(ModuleBase[AnalogInputPayload]):
    """Typed helper for analog input modules."""

    def __init__(self, device: "ConnectorX", module_id: str):
        super().__init__(device, module_id)

    def parse(self, entry: NewDataInfo) -> AnalogInputPayload:
        payload = AnalogInputPayload()
        if not entry.data:
            return payload

        data = entry.data
        if entry.len >= 2:
            payload.raw_value = (data[0] & 0xFF) | ((data[1] & 0xFF) << 8)
        if entry.len >= 6:
            payload.scaled_value = (
                (data[2] & 0xFF)
                | ((data[3] & 0xFF) << 8)
                | ((data[4] & 0xFF) << 16)
                | ((data[5] & 0xFF) << 24)
            )
        return payload
