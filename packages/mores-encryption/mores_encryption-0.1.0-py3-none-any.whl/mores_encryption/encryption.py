import base64
import logging
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure module-level logger
logger = logging.getLogger(__name__)

class EncryptionService:
    """
    AES-128 (Fernet standard) encryption service for securing sensitive data.

    This service implements the Fernet symmetric encryption algorithm, which is built on top of 
    AES-128 in CBC mode with a 128-bit HMAC using SHA256. This ensures both confidentiality 
    and integrity of the data.

    Key Features:
        - Automatic Key Management: Generates a new key if ENCRYPTION_KEY is not provided.
        - Deterministic Searching: Supports deterministic hashing for searching encrypted fields (e.g., email).
        - Safe Storage: Uses URL-safe Base64 encoding for all outputs.

    Environment Variables:
        ENCRYPTION_KEY (str): Base64-encoded 32-byte key for Fernet encryption.
    """
    
    _key: Optional[bytes] = None
    _cipher: Optional[Fernet] = None
    
    @classmethod
    def reset(cls) -> None:
        """
        Resets the internally cached key and cipher instance.

        This method is primarily useful for testing purposes or scenarios where the encryption
        key needs to be rotated or reloaded at runtime.
        """
        cls._key = None
        cls._cipher = None
    
    @classmethod
    def _get_or_create_key(cls) -> bytes:
        """
        Retrieves the encryption key from the environment or generates a new one.

        If 'ENCRYPTION_KEY' is not found in the environment variables, a new random key 
        is generated and a warning is logged.

        Returns:
            bytes: The 32-byte encryption key (URL-safe base64 encoded).

        Raises:
            Exception: If key retrieval or generation fails unexpectedly.
        """
        try:
            key_b64 = os.getenv('ENCRYPTION_KEY')
            if key_b64:
                return key_b64.encode()
            
            # Fallback: Generate new key
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Please add 'ENCRYPTION_KEY' to your .env file to persist it.")
            return key
        except Exception as e:
            logger.critical(f"Failed to generate or retrieve encryption key: {e}")
            raise
    
    @classmethod
    def _get_cipher(cls) -> Fernet:
        """
        Retrieves or creates the Fernet cipher singleton instance.

        This method implements a singleton pattern to avoid the overhead of re-initializing 
        the cipher on every operation.

        Returns:
            Fernet: An initialized Fernet cipher instance.
        """
        if cls._cipher is None:
            cls._key = cls._get_or_create_key()
            # Fernet expects the key as a string (if it was read as bytes, decode it)
            key_str = cls._key.decode() if isinstance(cls._key, bytes) else cls._key
            cls._cipher = Fernet(key_str)
            logger.info("EncryptionService initialized successfully.")
        return cls._cipher
    
    @staticmethod
    def encrypt(data: str) -> str:
        """
        Encrypts a plaintext string using AES-128 (Fernet).

        Args:
            data (str): The plaintext string to encrypt.

        Returns:
            str: The URL-safe Base64-encoded ciphertext. Returns an empty string if the input is empty.

        Raises:
            Exception: If the encryption process fails.
        """
        try:
            if not data:
                return ""
            cipher = EncryptionService._get_cipher()
            # Fernet.encrypt logic:
            # 1. Encrypts data
            # 2. Returns bytes (already URL-safe Base64 encoded)
            encrypted_bytes = cipher.encrypt(data.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.critical(f"Encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """
        Decrypts a URL-safe Base64-encoded ciphertext.

        Args:
            encrypted_data (str): The ciphertext string to decrypt.

        Returns:
            str: The original plaintext string. Returns an empty string if the input is empty.

        Raises:
            Exception: If decryption fails (e.g., invalid key, corrupted data).
        """
        try:
            if not encrypted_data:
                return ""
            cipher = EncryptionService._get_cipher()
            # Fernet.decrypt expects bytes (URL-safe Base64 encoded)
            decrypted = cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.critical(f"Decryption failed: {e}")
            raise
    
    @staticmethod
    def hash(data: str, salt: str, iterations: int = 200_000) -> str:
        """
        Generates a deterministic hash of data for secure searching.

        Unlike standard encryption (which is randomized), this method uses PBKDF2 
        to ensure that the same data input always produces the same hash given the same salt.

        Args:
            data (str): The data to hash.
            salt (str): The salt to use for hashing.
            iterations (int): Number of PBKDF2 iterations (recommended: 200,000+).

        Returns:
            str: The URL-safe Base64-encoded hash of the data.

        Raises:
            Exception: If the hashing process fails.
        """
        try:
            salt_bytes = salt.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=iterations,
            )
            data_hash = kdf.derive(data.encode())
            return base64.urlsafe_b64encode(data_hash).decode()
        except Exception as e:
            logger.critical(f"Deterministic hashing failed: {e}")
            raise

# Global instance of the service
encryption_service = EncryptionService()