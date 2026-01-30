"""AWS KMS encryption and decryption utilities."""

from typing import TYPE_CHECKING, Union, cast

if TYPE_CHECKING:
    try:
        from mypy_boto3_kms import KMSClient
    except ImportError:
        from typing import Any

        KMSClient = Any
else:
    from typing import Any

    KMSClient = Any


class KMSEncryptor:
    """Encryptor and decryptor using AWS KMS."""

    @staticmethod
    def encrypt(plaintext: Union[str, bytes], kms_key_arn: str, kms_client: KMSClient) -> bytes:
        """
        Encrypt plaintext using AWS KMS.

        Args:
            plaintext: The data to encrypt. Can be a string or bytes.
            kms_key_arn: The ARN of the KMS key to use for encryption.
            kms_client: The boto3 KMS client instance.

        Returns:
            bytes: The encrypted ciphertext blob.

        Example:
            >>> import boto3
            >>> kms = boto3.client('kms')
            >>> encryptor = KMSEncryptor()
            >>> ciphertext = encryptor.encrypt("secret data", "arn:aws:kms:...", kms)
        """
        # Convert string to bytes if necessary
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode("utf-8")
        else:
            plaintext_bytes = plaintext

        response = kms_client.encrypt(KeyId=kms_key_arn, Plaintext=plaintext_bytes)
        return cast(bytes, response["CiphertextBlob"])

    @staticmethod
    def decrypt(ciphertext: bytes, kms_key_arn: str, kms_client: KMSClient) -> bytes:
        """
        Decrypt ciphertext using AWS KMS.

        Args:
            ciphertext: The encrypted ciphertext blob to decrypt.
            kms_key_arn: The ARN of the KMS key (kept for API consistency;
                the key is automatically determined from the ciphertext).
            kms_client: The boto3 KMS client instance.

        Returns:
            bytes: The decrypted plaintext.

        Example:
            >>> import boto3
            >>> kms = boto3.client('kms')
            >>> encryptor = KMSEncryptor()
            >>> plaintext = encryptor.decrypt(ciphertext_blob, "arn:aws:kms:...", kms)
            >>> plaintext_str = plaintext.decode('utf-8')
        """
        # Note: KeyId is not needed for decrypt as it's embedded in the ciphertext blob
        response = kms_client.decrypt(CiphertextBlob=ciphertext)
        return cast(bytes, response["Plaintext"])
