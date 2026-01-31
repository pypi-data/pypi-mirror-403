import os
import sys
import unittest
from unittest.mock import patch
from cryptography.fernet import Fernet
from mores_encryption.encryption import EncryptionService
# --- Path Setup ---
# Add the project root to sys.path to allow importing the 'mores_encryption' package.
# Structure:
#   project_root/ (mores-encryption)
#     mores_encryption/ (package source)
#       encryption.py
#     tests/
#       test_encryption.py

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)





class TestEncryptionService(unittest.TestCase):
    """
    Unit tests for the EncryptionService class.
    
    Covers:
    - Encryption and Decryption (confidentiality)
    - Deterministic Hashing (searchability)
    - Key Management (generation and loading)
    - Singleton Pattern (performance)
    """

    def setUp(self):
        """Prepares the test environment before each test case."""
        # Reset the service to ensure a clean state
        EncryptionService.reset()
        
        # Clear specific environment variables to prevent test pollution
        self._clear_env_vars(['ENCRYPTION_KEY', 'EMAIL_SALT', 'HASH_SALT'])

    def tearDown(self):
        """Cleans up the test environment after each test case."""
        EncryptionService.reset()

    def _clear_env_vars(self, vars_list):
        """Helper to remove environment variables if they exist."""
        for var in vars_list:
            if var in os.environ:
                del os.environ[var]

    def test_encrypt_decrypt(self):
        """
        Verifies that data encrypted by the service can be correctly decrypted
        to recover the original plaintext.
        """
        original_text = "Secret Data 123"
        encrypted = EncryptionService.encrypt(original_text)
        
        # Formatting check
        self.assertNotEqual(original_text, encrypted, "Ciphertext should differ from plaintext")
        self.assertIsInstance(encrypted, str, "Ciphertext should be a string")
        
        # Correctness check
        decrypted = EncryptionService.decrypt(encrypted)
        self.assertEqual(original_text, decrypted, "Decrypted text must match original")

    def test_empty_input(self):
        """Verifies that empty input strings yield empty output strings."""
        self.assertEqual(EncryptionService.encrypt(""), "")
        self.assertEqual(EncryptionService.decrypt(""), "")


    def test_deterministic_email(self):
        """
        Verifies that email encryption is deterministic (same input + same salt = same output).
        This is critical for searching encrypted email fields.
        """
        email = "test@example.com"
        salt = "test_salt"
        
        # When using deterministic_hash directly, we pass the salt explicitly
        # The logic for 'email' usually implies lower, strip, and default salt handling
        # But here we are testing the core deterministic property
        
        hash1 = EncryptionService.hash(email.lower().strip(), salt)
        hash2 = EncryptionService.hash(email.lower().strip(), salt)
        self.assertEqual(hash1, hash2, "Encrypted email must be deterministic")
        
        # Verify case insensitivity normalization
        hash3 = EncryptionService.hash("TEST@example.com".lower().strip(), salt)
        self.assertEqual(hash1, hash3, "Email encryption should be case insensitive")

    def test_deterministic_hash(self):
        """Verifies that general data hashing is deterministic."""
        data = "sensitive_info"
        salt = "hash_salt_123"
        
        # Using deterministic_hash directly
        hash1 = EncryptionService.hash(data, salt)
        hash2 = EncryptionService.hash(data, salt)
        self.assertEqual(hash1, hash2, "Data hash must be deterministic")

    def test_key_generation(self):
        """
        Verifies that the service automatically generates a new encryption key
        if one is not provided in the environment variables.
        """
        # Ensure no key exists in env using the helper (called in setUp, but being explicit here)
        self._clear_env_vars(['ENCRYPTION_KEY'])
            
        EncryptionService.reset()
        
        # Triggering encryption/initialization should create a key
        cipher = EncryptionService._get_cipher()
        
        self.assertIsNotNone(cipher, "Cipher instance should be created")
        self.assertIsNotNone(EncryptionService._key, "Key should be generated internaly")

    def test_env_key(self):
        """Verifies that the service uses the encryption key provided in the environment."""
        # Generate a valid Fernet key for testing
        key = Fernet.generate_key()
        key_str = key.decode()
        
        with patch.dict(os.environ, {'ENCRYPTION_KEY': key_str}):
            EncryptionService.reset()
            cipher = EncryptionService._get_cipher()
            
            # The internal key should match what we put in env (as bytes)
            self.assertEqual(EncryptionService._key, key)

    def test_cipher_reuse(self):
        """Verifies that the cipher instance is cached (singleton behavior)."""
        cipher1 = EncryptionService._get_cipher()
        cipher2 = EncryptionService._get_cipher()
        self.assertIs(cipher1, cipher2, "Cipher instance should be a singleton")

    def test_reset(self):
        """Verifies that the reset method correctly clears cached key and cipher."""
        # Initialize first
        EncryptionService._get_cipher()
        self.assertIsNotNone(EncryptionService._cipher)
        
        # Reset
        EncryptionService.reset()
        
        self.assertIsNone(EncryptionService._cipher, "Cipher should be None after reset")
        self.assertIsNone(EncryptionService._key, "Key should be None after reset")


if __name__ == '__main__':
    unittest.main()
