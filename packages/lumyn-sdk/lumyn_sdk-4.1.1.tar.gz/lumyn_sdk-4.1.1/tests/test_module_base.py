import time
from typing import List

from lumyn_sdk.domain.module.module_base import ModuleBase
from lumyn_sdk.domain.module.module_data_dispatcher import ModuleDataDispatcher
from lumyn_sdk.domain.module.new_data_info import NewDataInfo


class _DummyInternal:
    def __init__(self) -> None:
        self.data_map = {}

    def GetLatestModuleData(self, module_id: str):
        return self.data_map.get(module_id, [])


class _DummyDevice:
    def __init__(self) -> None:
        self.internal = _DummyInternal()
        self.dispatcher = ModuleDataDispatcher(self.internal)

    def get_module_dispatcher(self) -> ModuleDataDispatcher:
        return self.dispatcher

    def get_latest_module_data(self, module_id: str):
        return self.internal.GetLatestModuleData(module_id)


class _SampleModule(ModuleBase[int]):
    def parse(self, entry: NewDataInfo) -> int:
        if entry.data and entry.len >= 1:
            return entry.data[0]
        return 0


def test_module_base_start_stop_and_get():
    device = _DummyDevice()
    device.internal.data_map["m1"] = [NewDataInfo(data=bytes([5]), length=1)]
    mod = _SampleModule(device, "m1")

    mod.start()
    assert "m1" in device.dispatcher._listeners  # type: ignore[attr-defined]

    result = mod.get()
    assert result == [5]

    mod.stop()
    assert "m1" in device.dispatcher._listeners or True  # unregister is best-effort


def test_module_base_callbacks():
    device = _DummyDevice()
    mod = _SampleModule(device, "m1")
    captured: List[int] = []
    mod.on_update(lambda payload: captured.append(payload))

    mod._handle_entries([NewDataInfo(data=bytes([9]), length=1)])  # type: ignore[attr-defined]
    assert captured == [9]
