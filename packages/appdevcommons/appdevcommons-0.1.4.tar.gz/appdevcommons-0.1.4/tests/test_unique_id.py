"""Tests for UniqueIdGenerator."""

from appdevcommons import UniqueIdGenerator


class TestUniqueIdGenerator:
    """Test cases for UniqueIdGenerator class."""

    def test_id_length_bytes_constant(self):
        """Test that ID_LENGTH_BYTES constant exists and is an integer."""
        assert hasattr(UniqueIdGenerator, "ID_LENGTH_BYTES")
        assert isinstance(UniqueIdGenerator.ID_LENGTH_BYTES, int)
        assert UniqueIdGenerator.ID_LENGTH_BYTES > 0

    def test_generate_id_returns_string(self):
        """Test that generate_id returns a string."""
        result = UniqueIdGenerator.generate_id()
        assert isinstance(result, str)

    def test_generate_id_returns_hex_format(self):
        """Test that generate_id returns a valid hexadecimal string."""
        result = UniqueIdGenerator.generate_id()
        # Hex string should only contain 0-9 and a-f
        assert all(c in "0123456789abcdef" for c in result.lower())
        # Should be able to convert back to bytes
        bytes_result = bytes.fromhex(result)
        assert len(bytes_result) == UniqueIdGenerator.ID_LENGTH_BYTES

    def test_generate_id_length(self):
        """Test that generate_id returns a string of correct length."""
        result = UniqueIdGenerator.generate_id()
        expected_length = UniqueIdGenerator.ID_LENGTH_BYTES * 2  # Each byte = 2 hex chars
        assert len(result) == expected_length

    def test_generate_id_uniqueness(self):
        """Test that generate_id produces different IDs on multiple calls."""
        id1 = UniqueIdGenerator.generate_id()
        id2 = UniqueIdGenerator.generate_id()
        id3 = UniqueIdGenerator.generate_id()

        # Very unlikely to be the same (probability is 1/(256^ID_LENGTH_BYTES))
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_generate_id_classmethod(self):
        """Test that generate_id can be called as a class method."""
        # Should work as class method
        result1 = UniqueIdGenerator.generate_id()
        assert isinstance(result1, str)

        # Should also work as instance method
        generator = UniqueIdGenerator()
        result2 = generator.generate_id()
        assert isinstance(result2, str)
