from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_datastore.constants import CHUNK_KEYS as CHUNK_KEYS
from gllm_datastore.encryptor.encryptor import BaseEncryptor as BaseEncryptor
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from gllm_inference.schema import Vector
from typing import Any

class EncryptionCapability:
    """Unified implementation of encryption capability.

    This class provides the shared encryption and decryption logic that is identical
    across all backend implementations. It handles:
    - Chunk content and metadata encryption/decryption
    - Preparation of encrypted chunks with plaintext embeddings
    - Encryption of update values

    Thread Safety:
        This class is designed to be thread-safe when used with thread-safe encryptors.
        The encryptor instance passed must be thread-safe for concurrent
        encryption/decryption operations. Methods in this class do not perform internal
        synchronization - thread safety is delegated to the underlying encryptor.

    Attributes:
        encryptor (BaseEncryptor): The encryptor instance to use for encryption/decryption.
            Must be thread-safe for concurrent operations.
        _encrypted_fields (set[str]): The set of fields to encrypt.
    """
    encryptor: Incomplete
    def __init__(self, encryptor: BaseEncryptor, encrypted_fields: set[str]) -> None:
        '''Initialize the encryption capability.

        Args:
            encryptor (BaseEncryptor): The encryptor instance to use for encryption.
            encrypted_fields (set[str]): The set of fields to encrypt. Supports:
                1. Content field: "content"
                2. Metadata fields using dot notation: "metadata.secret_key", "metadata.secret_value"
                Example: `{"content", "metadata.secret_key", "metadata.secret_value"}`
        '''
    @property
    def is_enabled(self) -> bool:
        """Check if encryption is enabled (has configured fields).

        Returns:
            bool: True if encryption fields are configured, False otherwise.
        """
    @property
    def encryption_config(self) -> set[str]:
        """Get the current encryption configuration.

        Returns:
            set[str]: Set of encrypted field names.
        """
    def encrypt_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Encrypt chunks if encryption is enabled.

        Args:
            chunks (list[Chunk]): List of chunks to encrypt.

        Returns:
            list[Chunk]: List of encrypted chunks.
        """
    def decrypt_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Decrypt chunks if encryption is enabled.

        Args:
            chunks (list[Chunk]): List of chunks to decrypt.

        Returns:
            list[Chunk]: List of decrypted chunks.
        """
    async def encrypt_embedded_chunks(self, chunks: list[Chunk], em_invoker: BaseEMInvoker) -> list[tuple[Chunk, Vector]]:
        """Encrypt chunks and generate embeddings from plaintext before encryption.

        Generates embeddings from plaintext content to ensure embeddings represent the original
        content rather than encrypted ciphertext. This is used when encryption is enabled.

        Args:
            chunks (list[Chunk]): List of chunks to encrypt and generate embeddings for.
            em_invoker (BaseEMInvoker): Embedding model invoker to generate embeddings.

        Returns:
            list[tuple[Chunk, Vector]]: List of tuples containing encrypted chunks and their
                corresponding vectors generated from plaintext.
        """
    def encrypt_update_values(self, update_values: dict[str, Any], content_field_name: str = ...) -> dict[str, Any]:
        '''Encrypt update values if encryption is enabled.

        This method encrypts content and metadata values in update_values according to the
        encryption configuration. It handles type conversion for non-string values before encryption.

        Args:
            update_values (dict[str, Any]): Dictionary of values to encrypt.
                Supports "content" and "metadata" keys.
            content_field_name (str, optional): The field name to use for content in the output.
                Defaults to CHUNK_KEYS.CONTENT. Useful for datastores like Elasticsearch
                that use "text" instead of "content".

        Returns:
            dict[str, Any]: Dictionary with encrypted values where applicable.
                The "content" key is mapped to content_field_name in the output.

        Raises:
            ValueError: If encryption fails for any field.
        '''
