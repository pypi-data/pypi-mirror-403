"""
Lumyn SDK Python Module

This module provides a comprehensive API for controlling Lumyn ConnectorX devices.
"""

from __future__ import annotations

# Import C++ bindings
from . import _bindings

# Expose submodules for tests and advanced usage
from ._bindings import command as _command
from ._bindings import event as _event
from ._bindings import module as _module
from ._bindings import util as _util
from ._bindings import config as _config
from ._bindings import connectorx as _connectorx

from ._bindings.connectorx import (
    Animation,
    AnimationBuilder,
    ImageSequenceBuilder,
    MatrixTextBuilder,
    MatrixTextScrollDirection as CppMatrixTextScrollDirection,
    MatrixTextFont as CppMatrixTextFont,
    MatrixTextAlign as CppMatrixTextAlign,
)
from ._bindings.config import (
    NetworkType,
    ZoneType,
    BitmapType,
    LumynConfiguration,
    ConfigBuilder,
    ParseConfig,
    SerializeConfigToJson,
)

# Re-export C++ matrix enums (override Python fallbacks if bindings are available)
try:
    MatrixTextScrollDirection = CppMatrixTextScrollDirection
    MatrixTextFont = CppMatrixTextFont
    MatrixTextAlign = CppMatrixTextAlign
except (ImportError, AttributeError):
    # Fall back to Python enums if C++ bindings not available
    from .enums import MatrixTextScrollDirection, MatrixTextFont, MatrixTextAlign

# Device classes
from .devices import ConnectorX, ConnectorXAnimate, list_available_ports

# Interfaces and callbacks
from .interfaces.i_event_callback import IEventCallback
from .interfaces.i_module_data_callback import IModuleDataCallback

# Domain classes
from .domain.event.event import Event
from .domain.module.new_data_info import NewDataInfo
from .domain.led.direct_led import DirectLED

# Typed module classes
from .modules import (
    AnalogInputModule,
    AnalogInputPayload,
    CustomModule,
    DigitalInputModule,
    DigitalInputPayload,
    VL53L1XModule,
    VL53L1XPayload,
)

# Enums (Python fallbacks for documentation, C++ bindings preferred)
from .enums import (
    EventType,
    Status,
    EventDisabledCause,
    EventErrorType,
    EventFatalErrorType,
    EventConnectionType,
    # NetworkType and ZoneType are imported from C++ bindings above
    # BitmapType is only available from C++ bindings
)

# Matrix text enums imported from C++ bindings above with fallback
# MatrixTextScrollDirection, MatrixTextFont, MatrixTextAlign

__version__: str = "4.1.1"  # x-release-please-version


# Convenience function to create ID from string
def createId(input: str) -> int:
    """Create a 16-bit ID from a string using the IDCreator."""
    return _bindings.util.hashing.IDCreator.createId(input)


# Main exports
__all__ = [
    # Device classes
    "ConnectorX",
    "ConnectorXAnimate",

    # Utility functions
    "list_available_ports",
    "createId",

    # Animation
    "Animation",
    "AnimationBuilder",
    "ImageSequenceBuilder",
    "MatrixTextBuilder",

    # Interfaces
    "IEventCallback",
    "IModuleDataCallback",

    # Domain classes
    "Event",
    "NewDataInfo",
    "DirectLED",

    # Config
    "ConfigBuilder",
    "SerializeConfigToJson",
    "ParseConfig",

    # Typed modules
    "AnalogInputModule",
    "AnalogInputPayload",
    "CustomModule",
    "DigitalInputModule",
    "DigitalInputPayload",
    "VL53L1XModule",
    "VL53L1XPayload",

    # Enums
    "EventType",
    "Status",
    "EventDisabledCause",
    "EventErrorType",
    "EventFatalErrorType",
    "EventConnectionType",
    "ZoneType",
    "NetworkType",
    "BitmapType",
    "MatrixTextScrollDirection",
    "MatrixTextFont",
    "MatrixTextAlign",

    # Config
    "ConfigBuilder",
    "LumynConfiguration",
    "SerializeConfigToJson",
    "ParseConfig",

    # Version
    "__version__",
]
