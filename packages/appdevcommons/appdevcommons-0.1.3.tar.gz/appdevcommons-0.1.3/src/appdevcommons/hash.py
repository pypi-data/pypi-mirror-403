"""Hash generation utilities."""

import hashlib


class HashGenerator:
    """Generator for SHA256 hash values."""

    HASH_ALGORITHM = "sha256"  # SHA256 algorithm

    @classmethod
    def generate_hash(cls, data: str | bytes) -> str:
        """
        Generate a SHA256 hash of the input data.

        Takes input data as a string or bytes and returns its SHA256 hash
        as a hexadecimal string.

        Args:
            data: Input data to hash. Can be a string or bytes.

        Returns:
            str: A hexadecimal string representation of the SHA256 hash.
                Length will be 64 characters (SHA256 produces 256 bits = 32 bytes = 64 hex chars).

        Example:
            >>> generator = HashGenerator()
            >>> hash_str = generator.generate_hash("hello world")
            >>> len(hash_str) == 64
            True
            >>> hash_str2 = generator.generate_hash("hello world")
            >>> hash_str == hash_str2
            True
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        hash_obj = hashlib.sha256(data)
        return hash_obj.hexdigest()
