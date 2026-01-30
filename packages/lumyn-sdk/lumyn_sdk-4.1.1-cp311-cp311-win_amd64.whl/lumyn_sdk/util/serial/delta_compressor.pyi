"""Type stubs for DeltaCompressor."""

from typing import Union


class DeltaCompressor:
    """XOR-based delta compressor for LED buffer updates.

    Delta compression works by computing the XOR difference between the current
    and previous buffer. Unchanged bytes become 0x00, making the data highly
    compressible and efficient to transmit.
    """

    @staticmethod
    def encode(
        current: Union[bytes, bytearray],
        previous: Union[bytes, bytearray],
        size: int = None
    ) -> bytes:
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
        ...

    @staticmethod
    def decode(
        delta: Union[bytes, bytearray],
        previous: Union[bytes, bytearray],
        size: int = None
    ) -> bytes:
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
        ...

    @staticmethod
    def is_all_zeros(data: Union[bytes, bytearray]) -> bool:
        """Check if delta buffer contains only zeros (no changes).

        Args:
            data: Buffer to check

        Returns:
            True if all bytes are zero (buffers are identical)
        """
        ...

    @staticmethod
    def count_changes(delta: Union[bytes, bytearray]) -> int:
        """Count the number of non-zero bytes in a delta buffer.

        Args:
            delta: Delta-encoded buffer

        Returns:
            Number of bytes that changed
        """
        ...

    @staticmethod
    def compression_ratio(delta: Union[bytes, bytearray]) -> float:
        """Calculate the compression ratio of a delta buffer.

        Args:
            delta: Delta-encoded buffer

        Returns:
            Ratio of unchanged bytes (0.0 = all changed, 1.0 = no changes)
        """
        ...
