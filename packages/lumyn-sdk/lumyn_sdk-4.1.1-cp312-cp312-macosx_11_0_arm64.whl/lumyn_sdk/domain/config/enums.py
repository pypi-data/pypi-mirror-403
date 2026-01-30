"""
Configuration enums matching Java vendordep.
"""

from enum import Enum


class NetworkType(Enum):
    """Network connection type"""
    USB = "usb"
    UART = "uart"
    I2C = "i2c"
    CAN = "can"


class ZoneType(Enum):
    """LED zone type"""
    STRIP = "strip"
    MATRIX = "matrix"


class BitmapType(Enum):
    """Bitmap/image sequence type"""
    STATIC = "static"
    ANIMATED = "animated"
