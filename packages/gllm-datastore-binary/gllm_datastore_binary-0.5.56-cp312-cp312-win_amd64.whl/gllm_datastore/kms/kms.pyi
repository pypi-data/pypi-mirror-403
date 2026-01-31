from abc import ABC, abstractmethod

class BaseKeyManagementService(ABC):
    """Abstract base class for Key Management Service implementations.

    This interface defines the contract for KMS implementations that handle
    data encryption key (DEK) management and encryption/decryption operations.
    """
    @abstractmethod
    def get_dek(self) -> tuple[bytes, str]:
        """Retrieve or generate a Data Encryption Key (DEK) and its encrypted form.

        Returns:
            tuple[bytes, str]: A tuple containing (dek, encrypted_dek).

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
    @abstractmethod
    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        """Decrypt an encrypted Data Encryption Key (DEK).

        Args:
            encrypted_dek (bytes): The encrypted data encryption key.

        Returns:
            bytes: The decrypted data encryption key.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext data.

        Args:
            plaintext (bytes): The data to encrypt.

        Returns:
            bytes: The encrypted data.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext data.

        Args:
            ciphertext (bytes): The encrypted data to decrypt.

        Returns:
            bytes: The decrypted data.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
