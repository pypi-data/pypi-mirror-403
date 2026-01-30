"""
Delta Compressor for efficient LED buffer updates.

Uses XOR-based delta encoding to minimize bandwidth when updating LED buffers
by only transmitting the differences between frames.
"""

from typing import Union
import warnings

# Lazy-load C++ bindings
_cpp_delta_compressor = None


def _load_bindings():
    """Lazy load C++ DeltaCompressor bindings."""
    global _cpp_delta_compressor
    if _cpp_delta_compressor is not None:
        return True
    try:
        from lumyn_sdk import _cpp
        _cpp_delta_compressor = _cpp.serial.DeltaCompressor
        return True
    except (ImportError, AttributeError) as e:
        warnings.warn(f"C++ DeltaCompressor bindings not available: {e}")
        return False


class DeltaCompressor:
    """XOR-based delta compressor for LED buffer updates.

    Delta compression works by computing the XOR difference between the current
    and previous buffer. Unchanged bytes become 0x00, making the data highly
    compressible and efficient to transmit.

    Example:
        >>> prev = bytes([255, 0, 0, 0, 255, 0])  # Red, Green LEDs
        >>> curr = bytes([255, 0, 0, 0, 0, 255])  # Red, Blue LEDs
        >>> delta = DeltaCompressor.encode(curr, prev)
        >>> # delta = bytes([0, 0, 0, 0, 255, 255])  # Only green->blue changed
        >>> restored = DeltaCompressor.decode(delta, prev)
        >>> assert restored == curr
    """

    @staticmethod
    def encode(current: Union[bytes, bytearray],
               previous: Union[bytes, bytearray],
               size: int = None) -> bytes:
        """Encode the difference between current and previous buffers.

        Args:
            current: The new buffer data
            previous: The previous buffer data (same length as current)
            size: Optional size parameter (uses len(current) if not specified)

        Returns:
            Delta-encoded bytes (XOR of current and previous)

        Raises:
            ValueError: If buffer sizes don't match
        """
        current_bytes = bytes(current)
        previous_bytes = bytes(previous)

        if size is None:
            size = len(current_bytes)

        if len(current_bytes) != len(previous_bytes):
            raise ValueError(
                f"Buffer size mismatch: current={len(current_bytes)}, "
                f"previous={len(previous_bytes)}"
            )

        # Try C++ implementation first for performance
        if _load_bindings() and _cpp_delta_compressor is not None:
            return _cpp_delta_compressor.encode(current_bytes, previous_bytes, size)

        # Pure Python fallback (XOR encoding)
        return bytes(c ^ p for c, p in zip(current_bytes, previous_bytes))

    @staticmethod
    def decode(delta: Union[bytes, bytearray],
               previous: Union[bytes, bytearray],
               size: int = None) -> bytes:
        """Decode a delta buffer to restore the original data.

        Args:
            delta: The delta-encoded buffer (from encode())
            previous: The previous buffer data
            size: Optional size parameter (uses len(delta) if not specified)

        Returns:
            Decoded bytes (the original current buffer)

        Raises:
            ValueError: If buffer sizes don't match
        """
        delta_bytes = bytes(delta)
        previous_bytes = bytes(previous)

        if size is None:
            size = len(delta_bytes)

        if len(delta_bytes) != len(previous_bytes):
            raise ValueError(
                f"Buffer size mismatch: delta={len(delta_bytes)}, "
                f"previous={len(previous_bytes)}"
            )

        # Try C++ implementation first for performance
        if _load_bindings() and _cpp_delta_compressor is not None:
            return _cpp_delta_compressor.decode(delta_bytes, previous_bytes, size)

        # Pure Python fallback (XOR decoding - same as encoding)
        return bytes(d ^ p for d, p in zip(delta_bytes, previous_bytes))

    @staticmethod
    def is_all_zeros(data: Union[bytes, bytearray]) -> bool:
        """Check if delta buffer contains only zeros (no changes).

        Args:
            data: Buffer to check

        Returns:
            True if all bytes are zero (buffers are identical)
        """
        return all(b == 0 for b in data)

    @staticmethod
    def count_changes(delta: Union[bytes, bytearray]) -> int:
        """Count the number of non-zero bytes in a delta buffer.

        Useful for determining if delta compression is beneficial.

        Args:
            delta: Delta-encoded buffer

        Returns:
            Number of bytes that changed
        """
        return sum(1 for b in delta if b != 0)

    @staticmethod
    def compression_ratio(delta: Union[bytes, bytearray]) -> float:
        """Calculate the compression ratio of a delta buffer.

        Args:
            delta: Delta-encoded buffer

        Returns:
            Ratio of unchanged bytes (0.0 = all changed, 1.0 = no changes)
        """
        if len(delta) == 0:
            return 1.0
        zeros = sum(1 for b in delta if b == 0)
        return zeros / len(delta)
