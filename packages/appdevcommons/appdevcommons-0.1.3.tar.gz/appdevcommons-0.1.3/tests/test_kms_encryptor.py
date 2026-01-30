"""Tests for KMSEncryptor."""

from unittest.mock import MagicMock

from appdevcommons import KMSEncryptor


class TestKMSEncryptor:
    """Test cases for KMSEncryptor class."""

    def test_encrypt_with_string_plaintext(self):
        """Test that encrypt works with string plaintext."""
        kms_client = MagicMock()
        kms_client.encrypt.return_value = {"CiphertextBlob": b"encrypted_data"}

        result = KMSEncryptor.encrypt(
            "test plaintext", "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )

        assert isinstance(result, bytes)
        assert result == b"encrypted_data"
        kms_client.encrypt.assert_called_once()
        call_kwargs = kms_client.encrypt.call_args[1]
        assert call_kwargs["KeyId"] == "arn:aws:kms:us-east-1:123456789012:key/abc123"
        assert call_kwargs["Plaintext"] == b"test plaintext"

    def test_encrypt_with_bytes_plaintext(self):
        """Test that encrypt works with bytes plaintext."""
        kms_client = MagicMock()
        kms_client.encrypt.return_value = {"CiphertextBlob": b"encrypted_data"}

        plaintext_bytes = b"test plaintext"
        result = KMSEncryptor.encrypt(
            plaintext_bytes, "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )

        assert isinstance(result, bytes)
        assert result == b"encrypted_data"
        kms_client.encrypt.assert_called_once()
        call_kwargs = kms_client.encrypt.call_args[1]
        assert call_kwargs["Plaintext"] == plaintext_bytes

    def test_decrypt(self):
        """Test that decrypt works correctly."""
        kms_client = MagicMock()
        kms_client.decrypt.return_value = {"Plaintext": b"decrypted_data"}

        ciphertext = b"encrypted_blob"
        result = KMSEncryptor.decrypt(
            ciphertext, "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )

        assert isinstance(result, bytes)
        assert result == b"decrypted_data"
        kms_client.decrypt.assert_called_once()
        call_kwargs = kms_client.decrypt.call_args[1]
        assert call_kwargs["CiphertextBlob"] == ciphertext
        # KeyId is not passed to decrypt as it's embedded in the ciphertext

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt and decrypt work together for a roundtrip."""
        kms_client = MagicMock()

        # Mock encrypt to return a ciphertext
        original_plaintext = "test data"
        ciphertext_blob = b"mock_ciphertext"
        kms_client.encrypt.return_value = {"CiphertextBlob": ciphertext_blob}

        # Encrypt
        encrypted = KMSEncryptor.encrypt(
            original_plaintext, "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert encrypted == ciphertext_blob

        # Mock decrypt to return the original plaintext
        kms_client.decrypt.return_value = {"Plaintext": original_plaintext.encode("utf-8")}

        # Decrypt
        decrypted = KMSEncryptor.decrypt(
            encrypted, "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert decrypted == original_plaintext.encode("utf-8")

    def test_encrypt_static_method(self):
        """Test that encrypt can be called as a static method."""
        kms_client = MagicMock()
        kms_client.encrypt.return_value = {"CiphertextBlob": b"encrypted"}

        # Should work as static method
        result1 = KMSEncryptor.encrypt(
            "test", "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert isinstance(result1, bytes)

        # Should also work as instance method
        encryptor = KMSEncryptor()
        result2 = encryptor.encrypt(
            "test", "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert isinstance(result2, bytes)

    def test_decrypt_static_method(self):
        """Test that decrypt can be called as a static method."""
        kms_client = MagicMock()
        kms_client.decrypt.return_value = {"Plaintext": b"decrypted"}

        # Should work as static method
        result1 = KMSEncryptor.decrypt(
            b"ciphertext", "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert isinstance(result1, bytes)

        # Should also work as instance method
        encryptor = KMSEncryptor()
        result2 = encryptor.decrypt(
            b"ciphertext", "arn:aws:kms:us-east-1:123456789012:key/abc123", kms_client
        )
        assert isinstance(result2, bytes)
