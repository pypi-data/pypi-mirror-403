from __future__ import annotations

from typing import Callable, Generic, TypeVar

from ..domain.module.module_base import ModuleBase
from ..domain.module.new_data_info import NewDataInfo

T = TypeVar("T")


class CustomModule(ModuleBase[T], Generic[T]):
    """Typed helper with user-provided parser."""

    def __init__(self, device: "ConnectorX", module_id: str, parser: Callable[[NewDataInfo], T]):
        super().__init__(device, module_id)
        self._parser = parser

    def parse(self, entry: NewDataInfo) -> T:
        return self._parser(entry)
