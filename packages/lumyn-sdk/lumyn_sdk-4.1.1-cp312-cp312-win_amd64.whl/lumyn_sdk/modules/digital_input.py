from __future__ import annotations

from dataclasses import dataclass

from ..domain.module.module_base import ModuleBase
from ..domain.module.new_data_info import NewDataInfo


@dataclass
class DigitalInputPayload:
    """Parsed digital input payload."""

    state: int = 0  # 0 = LOW, non-zero = HIGH


class DigitalInputModule(ModuleBase[DigitalInputPayload]):
    """Typed helper for digital input modules."""

    def __init__(self, device: "ConnectorX", module_id: str):
        super().__init__(device, module_id)

    def parse(self, entry: NewDataInfo) -> DigitalInputPayload:
        payload = DigitalInputPayload()
        if entry.data and entry.len >= 1:
            payload.state = entry.data[0]
        return payload
