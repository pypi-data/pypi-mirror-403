from _typeshed import Incomplete
from gllm_datastore.encryptor.aes_gcm_encryptor import AESGCMEncryptor as AESGCMEncryptor
from gllm_datastore.encryptor.encryptor import BaseEncryptor as BaseEncryptor
from gllm_datastore.kms.kms import BaseKeyManagementService as BaseKeyManagementService

class KmsEncryptor(BaseEncryptor):
    """KMS encryptor that uses KMS interface to manage encryption keys.

    This encryptor uses a KMS to generate and encrypt Data Encryption Keys (DEKs),
    then uses the DEK with AES-GCM to encrypt the actual plaintext data.

    Attributes:
        kms (BaseKeyManagementService): The KMS instance for key management.
    """
    kms: Incomplete
    def __init__(self, kms: BaseKeyManagementService) -> None:
        """Initialize the KMS encryptor.

        Args:
            kms (BaseKeyManagementService): The KMS instance to use for key management.
        """
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using KMS-managed DEK with AES-GCM.

        This method implements envelope encryption:
        1. Get a new DEK and its encrypted form from KMS
        2. Use the DEK to encrypt plaintext with AES-GCM
        3. Construct JSON containing encrypted plaintext and encrypted DEK
        4. Base64 encode the JSON and return

        Args:
            plaintext (str): The plaintext data to encrypt.

        Returns:
            str: Base64-encoded JSON containing encrypted data and encrypted DEK.

        Raises:
            Exception: If KMS fails to generate DEK.
            ValueError: If AES-GCM encryption fails.
        """
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext using KMS-managed DEK with AES-GCM.

        This method reverses the envelope encryption process:
        1. Base64 decode the ciphertext to get JSON
        2. Parse JSON to extract encrypted data and encrypted DEK
        3. Decrypt the DEK using KMS
        4. Use the decrypted DEK to decrypt the data with AES-GCM

        Args:
            ciphertext (str): Base64-encoded JSON containing encrypted data and encrypted DEK.

        Returns:
            str: The decrypted plaintext.

        Raises:
            binascii.Error: If ciphertext is not valid base64.
            json.JSONDecodeError: If decoded data is not valid JSON.
            KeyError: If envelope is missing required fields.
            Exception: If KMS fails to decrypt DEK.
            ValueError: If AES-GCM decryption fails.
        """
