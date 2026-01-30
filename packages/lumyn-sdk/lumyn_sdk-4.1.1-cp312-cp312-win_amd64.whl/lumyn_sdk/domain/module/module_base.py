"""
Typed module base class mirroring Java's ModuleBase<T>.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Generic, List, Optional, TypeVar

from .new_data_info import NewDataInfo
from .module_data_dispatcher import ModuleDataDispatcher

T = TypeVar("T")


class ModuleBase(Generic[T], ABC):
    """Base class for typed module helpers."""

    def __init__(self, device: "ConnectorX", module_id: str):
        self._device = device
        self._module_id = module_id
        self._callbacks: List[Callable[[T], None]] = []
        self._running = False
        self._listener: Optional[Callable[[List[NewDataInfo]], None]] = None

    def start(self) -> None:
        """Start receiving module data callbacks.
        
        Raises:
            RuntimeError: If module dispatcher is unavailable.
        """
        if self._running:
            return

        dispatcher = self._get_dispatcher()
        if dispatcher is None:
            raise RuntimeError("Module dispatcher unavailable")

        self._running = True
        self._listener = lambda entries: self._handle_entries(entries)
        dispatcher.register_listener(self._module_id, self._listener)

    def stop(self) -> None:
        """Stop receiving module data callbacks."""
        dispatcher = self._get_dispatcher()
        if dispatcher and self._listener:
            dispatcher.unregister_listener(self._module_id, self._listener)
        self._running = False
        self._listener = None

    def get(self) -> List[T]:
        """
        Manually fetch the latest module data and return parsed payloads.

        Note: This mirrors the Java behavior of draining the queue.
        
        Returns:
            List of parsed payloads. Empty list if no data available.
        """
        raw_entries = self._device.get_latest_module_data(self._module_id)
        parsed: List[T] = [self.parse(entry) for entry in raw_entries]
        return parsed

    def on_update(self, callback: Callable[[T], None]) -> None:
        """Register a callback to receive parsed module data."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[T], None]) -> None:
        """Remove a previously registered callback.
        
        Does nothing if callback was not registered.
        """
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    @abstractmethod
    def parse(self, entry: NewDataInfo) -> T:
        """Parse raw data into typed payload."""
        raise NotImplementedError

    # Internal helpers
    def _get_dispatcher(self) -> Optional[ModuleDataDispatcher]:
        return getattr(self._device, "get_module_dispatcher", lambda: None)()

    def _handle_entries(self, entries: List[NewDataInfo]) -> None:
        if not entries:
            return
        for entry in entries:
            try:
                payload = self.parse(entry)
            except Exception:
                continue

            for cb in list(self._callbacks):
                try:
                    cb(payload)
                except Exception:
                    # Swallow exceptions from user callbacks to keep dispatch alive
                    pass
