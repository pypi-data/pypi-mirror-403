"""Unique ID generation utilities."""

import secrets


class UniqueIdGenerator:
    """Generator for unique identifiers using cryptographically secure random bytes."""

    ID_LENGTH_BYTES = 16  # Default to 16 bytes (128 bits), similar to UUID4

    @classmethod
    def generate_id(cls) -> str:
        """
        Generate a unique ID using random bytes.

        Generates random bytes up to ID_LENGTH_BYTES and returns them as a hexadecimal string.

        Returns:
            str: A hexadecimal string representation of the random bytes.
                Length will be ID_LENGTH_BYTES * 2 (each byte = 2 hex characters).

        Example:
            >>> generator = UniqueIdGenerator()
            >>> id_str = generator.generate_id()
            >>> len(id_str) == UniqueIdGenerator.ID_LENGTH_BYTES * 2
            True
        """
        random_bytes = secrets.token_bytes(cls.ID_LENGTH_BYTES)
        return random_bytes.hex()
