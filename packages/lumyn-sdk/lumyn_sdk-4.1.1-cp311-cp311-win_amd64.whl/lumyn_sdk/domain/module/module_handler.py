"""
ModuleHandler - Module/sensor data interface using C++ SDK.

Provides Python-friendly methods for registering and receiving module data.
"""

from typing import Callable, List, Optional


class ModuleHandler:
    """
    Handler for module/sensor data operations.
    
    Wraps C++ SDK module methods to provide a clean Python API.
    """

    def __init__(self, cpp_device):
        """
        Initialize module handler.
        
        Args:
            cpp_device: The C++ SDK ConnectorXInternal instance
        """
        self._cpp_device = cpp_device
        self._module_callbacks = {}

    def register_module(self, module_id: str, callback: Callable) -> None:
        """
        Register a callback for module data.
        
        Args:
            module_id: Module identifier (e.g., "sensor1", "digital-1")
            callback: Function to call with module data
        """
        # Store callback
        self._module_callbacks[module_id] = callback
        
        # Register with C++ SDK
        if self._cpp_device and hasattr(self._cpp_device, 'RegisterModule'):
            self._cpp_device.RegisterModule(module_id, callback)

    def unregister_module(self, module_id: str) -> None:
        """
        Unregister a module callback.
        
        Args:
            module_id: Module identifier to unregister
        """
        if module_id in self._module_callbacks:
            del self._module_callbacks[module_id]

    def get_latest_data(self, module_id: str) -> Optional[bytes]:
        """
        Get the latest data for a module.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Latest module data as bytes, or None if no data available
        """
        if self._cpp_device and hasattr(self._cpp_device, 'GetLatestModuleData'):
            try:
                data = self._cpp_device.GetLatestModuleData(module_id)
                return data if data else None
            except Exception:
                return None
        return None

    def set_polling_enabled(self, enabled: bool) -> None:
        """
        Enable/disable automatic module polling.
        
        Args:
            enabled: Whether to enable polling
        """
        if self._cpp_device and hasattr(self._cpp_device, 'SetModulePollingEnabled'):
            self._cpp_device.SetModulePollingEnabled(enabled)

    def poll_modules(self) -> None:
        """Poll modules once to get latest data."""
        if self._cpp_device and hasattr(self._cpp_device, 'PollModules'):
            self._cpp_device.PollModules()
