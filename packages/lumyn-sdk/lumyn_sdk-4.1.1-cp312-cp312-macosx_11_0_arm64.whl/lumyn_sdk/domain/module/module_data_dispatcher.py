"""
Central dispatcher for module data polling.

Mirrors the Java ModuleDataDispatcher by maintaining a single polling thread
that drains module data from the device and dispatches it to all listeners.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict, List, Optional, Set

from .new_data_info import NewDataInfo

ModuleDataListener = Callable[[List[NewDataInfo]], None]


class ModuleDataDispatcher:
    """Poll module data once and dispatch to all listeners per module ID."""

    def __init__(self, internal: Optional[object]) -> None:
        self._internal = internal
        self._listeners: Dict[str, Set[ModuleDataListener]] = {}
        self._lock = threading.Lock()
        self._polling = False
        self._thread: Optional[threading.Thread] = None
        self._poll_interval_ms = 10

    def register_listener(self, module_id: str, listener: ModuleDataListener) -> None:
        if not module_id or listener is None:
            return
        with self._lock:
            self._listeners.setdefault(module_id, set()).add(listener)

    def unregister_listener(self, module_id: str, listener: ModuleDataListener) -> None:
        if not module_id or listener is None:
            return
        with self._lock:
            listeners = self._listeners.get(module_id)
            if listeners and listener in listeners:
                listeners.remove(listener)
                if not listeners:
                    self._listeners.pop(module_id, None)

    def set_poll_interval(self, interval_ms: int) -> None:
        self._poll_interval_ms = max(1, int(interval_ms))

    def start(self) -> None:
        if self._polling:
            return
        self._polling = True
        self._thread = threading.Thread(
            target=self._poll_loop, name="Lumyn-ModuleDataDispatcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._polling = False
        if self._thread:
            self._thread.join(timeout=0.5)
            self._thread = None

    def is_polling(self) -> bool:
        return self._polling

    def close(self) -> None:
        self.stop()
        with self._lock:
            self._listeners.clear()

    def _poll_loop(self) -> None:
        while self._polling:
            try:
                with self._lock:
                    items = list(self._listeners.items())
                for module_id, listeners_snapshot in items:
                    if not listeners_snapshot:
                        continue
                    entries = self._fetch_entries(module_id)
                    if not entries:
                        continue
                    # Re-check listeners under lock to avoid race with unregister
                    with self._lock:
                        current_listeners = self._listeners.get(
                            module_id, set())
                        listeners_to_call = list(
                            listeners_snapshot & current_listeners)

                    for listener in listeners_to_call:
                        try:
                            listener(entries)
                        except Exception:
                            # Swallow to keep polling alive
                            pass
                time.sleep(self._poll_interval_ms / 1000.0)
            except Exception:
                # Keep polling alive despite unexpected errors
                time.sleep(self._poll_interval_ms / 1000.0)

    def _fetch_entries(self, module_id: str) -> List[NewDataInfo]:
        """Fetch module data from C++ bindings and convert to NewDataInfo objects.

        The C++ GetLatestModuleData returns a list of dicts with 'id' and 'data' keys.
        We ignore the 'id' field (internal packet ID) and just use data/length.
        """
        try:
            raw_list = None
            if self._internal and hasattr(self._internal, "GetLatestModuleData"):
                raw_list = self._internal.GetLatestModuleData(
                    module_id)  # type: ignore[attr-defined]
            elif self._internal and hasattr(self._internal, "TryPopModuleDataRaw"):
                module_key = self._create_module_key(module_id)
                if module_key is None:
                    return []
                raw_list = self._internal.TryPopModuleDataRaw(
                    module_key)  # type: ignore[attr-defined]
        except Exception:
            return []

        if not raw_list:
            return []

        return self._convert_to_new_data_info(raw_list)

    @staticmethod
    def _create_module_key(module_id: str) -> Optional[int]:
        try:
            from ..._bindings.util import hashing as hashing_mod
        except Exception:
            return None
        try:
            return hashing_mod.IDCreator.createId(module_id)
        except Exception:
            return None

    @staticmethod
    def _convert_to_new_data_info(raw_list: list) -> List[NewDataInfo]:
        """Convert C++ binding output (list of dicts) to NewDataInfo objects."""
        entries: List[NewDataInfo] = []
        for item in raw_list:
            if isinstance(item, NewDataInfo):
                entries.append(item)
                continue

            # C++ binding returns dict with 'id' (packet id) and 'data' (bytes)
            data = None
            if isinstance(item, (bytes, bytearray, memoryview)):
                data = bytes(item)
            elif isinstance(item, dict):
                data = item.get("data")
            else:
                data = getattr(item, "data", None)

            if data is None:
                continue

            # Use actual data length
            length = len(data) if data else 0

            try:
                entries.append(NewDataInfo(data=data, length=length))
            except Exception:
                continue

        return entries
