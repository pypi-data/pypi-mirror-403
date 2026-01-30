"""
Python wrapper layer for configuration C++ bindings.

Provides convenience methods and Pythonic API on top of the C++ bindings.
"""

from typing import Optional


class DeviceConfigWrapper:
    """
    Python wrapper for LumynConfiguration C++ class.
    
    Adds convenience methods for JSON serialization/deserialization.
    """
    
    def __init__(self, cpp_config):
        """Wrap a C++ LumynConfiguration object."""
        self._cpp_config = cpp_config
    
    def to_json(self) -> str:
        """
        Serialize configuration to JSON string.
        
        Returns:
            JSON string representation of the configuration
        """
        from . import SerializeConfigToJson
        return SerializeConfigToJson(self._cpp_config)
    
    @staticmethod
    def from_json(json_str: str) -> Optional["DeviceConfigWrapper"]:
        """
        Deserialize configuration from JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            DeviceConfigWrapper if successful, None otherwise
        """
        from . import ParseConfig
        cpp_config = ParseConfig(json_str)
        if cpp_config:
            return DeviceConfigWrapper(cpp_config)
        return None
    
    @property
    def cpp_config(self):
        """Get the underlying C++ configuration object."""
        return self._cpp_config
    
    # Proxy common attributes
    @property
    def team_number(self):
        return self._cpp_config.teamNumber
    
    @property
    def network(self):
        return self._cpp_config.network
    
    @property
    def channels(self):
        return self._cpp_config.channels
    
    @property
    def sequences(self):
        return self._cpp_config.sequences
    
    @property
    def bitmaps(self):
        return self._cpp_config.bitmaps
    
    @property
    def modules(self):
        return self._cpp_config.sensors
    
    @property
    def groups(self):
        return self._cpp_config.animationGroups
