"""
Configuration package for Lumyn device configuration.

This package provides Python wrappers around the C++ configuration builder,
matching the Java vendordep API.
"""

try:
    from ...lumyn_sdk import (
        NetworkType,
        ZoneType,
        BitmapType,
        ConfigBuilder,
        LumynConfiguration,
        SerializeConfigToJson,
        ParseConfig,
    )
    _HAS_CPP_CONFIG = True
except ImportError:
    _HAS_CPP_CONFIG = False
    import warnings
    warnings.warn("C++ configuration bindings not available")

# Re-export for convenience
if _HAS_CPP_CONFIG:
    # Create Python-friendly alias
    DeviceConfig = LumynConfiguration

    __all__ = [
        # Enums
        "NetworkType",
        "ZoneType",
        "BitmapType",
        # Main classes
        "ConfigBuilder",
        "DeviceConfig",
        "LumynConfiguration",
        # Functions
        "SerializeConfigToJson",
        "ParseConfig",
    ]
else:
    __all__ = []
