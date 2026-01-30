import time

from lumyn_sdk.domain.module.module_data_dispatcher import ModuleDataDispatcher
from lumyn_sdk.domain.module.new_data_info import NewDataInfo


class _DummyInternal:
    def __init__(self) -> None:
        self.data_map = {}

    def GetLatestModuleData(self, module_id: str):
        return self.data_map.get(module_id, [])


def test_dispatcher_polls_and_dispatches():
    internal = _DummyInternal()
    dispatcher = ModuleDataDispatcher(internal)
    internal.data_map["mod"] = [NewDataInfo(
        module_id="mod", data=bytes([1]), length=1)]

    captured = []

    def listener(entries):
        for e in entries:
            captured.append(e.data[0])

    dispatcher.set_poll_interval(5)
    dispatcher.register_listener("mod", listener)
    dispatcher.start()  # Must manually start polling

    time.sleep(0.05)
    dispatcher.stop()

    assert captured, "Listener should receive at least one payload"


def test_dispatcher_unregister():
    internal = _DummyInternal()
    dispatcher = ModuleDataDispatcher(internal)
    internal.data_map["mod"] = [NewDataInfo(
        module_id="mod", data=bytes([2]), length=1)]

    captured = []

    def listener(entries):
        captured.extend(e.data[0] for e in entries)

    dispatcher.register_listener("mod", listener)
    dispatcher.unregister_listener("mod", listener)
    time.sleep(0.02)
    dispatcher.stop()

    # Since unregistered immediately, we should see no data captured
    assert captured == []
