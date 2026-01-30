"""Tests for HashGenerator."""

from appdevcommons import HashGenerator


class TestHashGenerator:
    """Test cases for HashGenerator class."""

    def test_hash_algorithm_constant(self):
        """Test that HASH_ALGORITHM constant exists and is a string."""
        assert hasattr(HashGenerator, "HASH_ALGORITHM")
        assert isinstance(HashGenerator.HASH_ALGORITHM, str)
        assert HashGenerator.HASH_ALGORITHM == "sha256"

    def test_generate_hash_returns_string(self):
        """Test that generate_hash returns a string."""
        result = HashGenerator.generate_hash("test data")
        assert isinstance(result, str)

    def test_generate_hash_returns_hex_format(self):
        """Test that generate_hash returns a valid hexadecimal string."""
        result = HashGenerator.generate_hash("test data")
        # Hex string should only contain 0-9 and a-f
        assert all(c in "0123456789abcdef" for c in result.lower())
        # SHA256 produces 64 hex characters (32 bytes)
        assert len(result) == 64

    def test_generate_hash_length(self):
        """Test that generate_hash returns a string of correct length."""
        result = HashGenerator.generate_hash("test data")
        # SHA256 produces 256 bits = 32 bytes = 64 hex characters
        assert len(result) == 64

    def test_generate_hash_deterministic(self):
        """Test that generate_hash produces the same hash for the same input."""
        data = "hello world"
        hash1 = HashGenerator.generate_hash(data)
        hash2 = HashGenerator.generate_hash(data)
        hash3 = HashGenerator.generate_hash(data)

        # Same input should produce same hash
        assert hash1 == hash2
        assert hash2 == hash3
        assert hash1 == hash3

    def test_generate_hash_different_inputs(self):
        """Test that generate_hash produces different hashes for different inputs."""
        hash1 = HashGenerator.generate_hash("hello")
        hash2 = HashGenerator.generate_hash("world")
        hash3 = HashGenerator.generate_hash("hello world")

        # Different inputs should produce different hashes
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3

    def test_generate_hash_with_bytes(self):
        """Test that generate_hash works with bytes input."""
        data_bytes = b"test data"
        result = HashGenerator.generate_hash(data_bytes)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_generate_hash_string_vs_bytes(self):
        """Test that generate_hash produces same hash for string and bytes of same content."""
        data_str = "test data"
        data_bytes = b"test data"
        hash_str = HashGenerator.generate_hash(data_str)
        hash_bytes = HashGenerator.generate_hash(data_bytes)
        # Should produce the same hash
        assert hash_str == hash_bytes

    def test_generate_hash_classmethod(self):
        """Test that generate_hash can be called as a class method."""
        # Should work as class method
        result1 = HashGenerator.generate_hash("test")
        assert isinstance(result1, str)

        # Should also work as instance method
        generator = HashGenerator()
        result2 = generator.generate_hash("test")
        assert isinstance(result2, str)
        # Same input should produce same result
        assert result1 == result2

    def test_generate_hash_known_value(self):
        """Test that generate_hash produces expected hash for known input."""
        # SHA256 of empty string
        empty_hash = HashGenerator.generate_hash("")
        assert len(empty_hash) == 64
        # Known SHA256 of empty string: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        expected_empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert empty_hash == expected_empty

        # SHA256 of "hello world"
        hello_hash = HashGenerator.generate_hash("hello world")
        # Known SHA256 of "hello world": b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
        expected_hello = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert hello_hash == expected_hello
