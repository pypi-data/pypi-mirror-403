"""
NewDataInfo class for module data handling

This class represents the structure for module data similar to the Java vendordep
NewDataInfo class, containing module ID, raw data array, and length.
"""

from typing import Optional


class NewDataInfo:
    """Data structure for module data information.

    Mirrors Java's ModuleDataEntry structure - contains raw data bytes and length.
    The module ID is implicit from context (which module you're querying).
    """

    def __init__(self, data: Optional[bytes] = None, length: Optional[int] = None, module_id: Optional[str] = None):
        """Initialize NewDataInfo

        Args:
            data: Raw data bytes
            length: Length of valid data in bytes (defaults to len(data))
            module_id: Optional module ID (for compatibility, not stored)
        """
        self.data = data if data is not None else b''
        self.len = length if length is not None else len(self.data)
        # module_id is accepted but not stored (for backward compatibility with tests)

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"NewDataInfo(len={self.len}, data={len(self.data)} bytes)"

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Module data: {self.len} bytes"
