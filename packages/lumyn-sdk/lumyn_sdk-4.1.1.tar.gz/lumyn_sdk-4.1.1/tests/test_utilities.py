"""
Tests for utility classes (IDCreator, MD5, CircularBuffer).

Verifies that utility classes are correctly exposed and functional.
"""

import pytest


class TestIDCreator:
    """Tests for IDCreator hashing utility."""

    def test_id_creator_exists(self, sdk):
        """IDCreator should be available."""
        assert hasattr(sdk._util.hashing, 'IDCreator')

    def test_create_id_method(self, sdk):
        """IDCreator should have createId method."""
        assert hasattr(sdk._util.hashing.IDCreator, 'createId')

    def test_create_id_returns_uint16(self, sdk):
        """createId should return a 16-bit integer."""
        result = sdk._util.hashing.IDCreator.createId("test_zone")

        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF, f"Result {result} out of uint16 range"

    def test_create_id_deterministic(self, sdk):
        """Same input should always produce same output."""
        input_str = "front_leds"

        hash1 = sdk._util.hashing.IDCreator.createId(input_str)
        hash2 = sdk._util.hashing.IDCreator.createId(input_str)

        assert hash1 == hash2, "Hashing should be deterministic"

    def test_create_id_different_inputs(self, sdk):
        """Different inputs should (usually) produce different outputs."""
        hash1 = sdk._util.hashing.IDCreator.createId("zone_a")
        hash2 = sdk._util.hashing.IDCreator.createId("zone_b")
        hash3 = sdk._util.hashing.IDCreator.createId("zone_c")

        # While collisions are possible, these short distinct strings should differ
        assert hash1 != hash2 or hash2 != hash3, \
            "Different inputs should produce different hashes"

    def test_create_id_empty_string(self, sdk):
        """Empty string should produce valid hash."""
        result = sdk._util.hashing.IDCreator.createId("")

        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF

    def test_create_id_special_characters(self, sdk):
        """Strings with special characters should hash correctly."""
        result = sdk._util.hashing.IDCreator.createId("zone-1_test.name")

        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF


class TestMD5:
    """Tests for MD5 hashing utility."""

    def test_md5_exists(self, sdk):
        """MD5 class should be available."""
        assert hasattr(sdk._util.hashing, 'MD5')

    def test_md5_hash_method(self, sdk):
        """MD5 should have hash method."""
        assert hasattr(sdk._util.hashing.MD5, 'hash')

    def test_md5_returns_16_bytes(self, sdk):
        """MD5 hash should return 16 bytes."""
        result = sdk._util.hashing.MD5.hash(b"test data")

        assert isinstance(result, bytes)
        assert len(result) == 16

    def test_md5_deterministic(self, sdk):
        """Same input should produce same hash."""
        data = b"hello world"

        hash1 = sdk._util.hashing.MD5.hash(data)
        hash2 = sdk._util.hashing.MD5.hash(data)

        assert hash1 == hash2

    def test_md5_different_inputs(self, sdk):
        """Different inputs should produce different hashes."""
        hash1 = sdk._util.hashing.MD5.hash(b"input1")
        hash2 = sdk._util.hashing.MD5.hash(b"input2")

        assert hash1 != hash2


class TestCircularBuffer:
    """Tests for CircularBuffer utility."""

    def test_circular_buffer_exists(self, sdk):
        """CircularBuffer should be available."""
        assert hasattr(sdk._util, 'CircularBuffer')

    def test_create_circular_buffer(self, sdk):
        """Should be able to create CircularBuffer with size."""
        buffer = sdk._util.CircularBuffer(1024)
        assert buffer is not None

    def test_buffer_capacity(self, sdk):
        """Buffer should report correct capacity."""
        capacity = 256
        buffer = sdk._util.CircularBuffer(capacity)

        assert buffer.capacity() == capacity

    def test_buffer_initially_empty(self, sdk):
        """New buffer should have size 0."""
        buffer = sdk._util.CircularBuffer(256)

        assert buffer.size() == 0
