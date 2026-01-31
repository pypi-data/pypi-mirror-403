"""
Fernet encryption for sensitive data like database passwords.

Usage:
    from constec.services import encrypt_password, decrypt_password

    # Encrypt
    encrypted = encrypt_password("my_password", fernet_key)

    # Decrypt
    password = decrypt_password(encrypted, fernet_key)

The FERNET_KEY should be stored in environment variables and never committed.
Generate a new key with:
    from cryptography.fernet import Fernet
    print(Fernet.generate_key().decode())
"""

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, key: str):
        """
        Initialize with Fernet key.

        Args:
            key: Fernet key as string (will be encoded to bytes)
        """
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted string

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        return self._fernet.decrypt(ciphertext.encode()).decode()


def encrypt_password(password: str, fernet_key: str) -> str:
    """
    Encrypt a password using Fernet symmetric encryption.

    Args:
        password: Plain text password
        fernet_key: Fernet encryption key

    Returns:
        Encrypted password (base64 encoded string)
    """
    service = EncryptionService(fernet_key)
    return service.encrypt(password)


def decrypt_password(encrypted_password: str, fernet_key: str) -> str:
    """
    Decrypt a password using Fernet symmetric encryption.

    Args:
        encrypted_password: Encrypted password (base64 encoded string)
        fernet_key: Fernet encryption key

    Returns:
        Decrypted password

    Raises:
        InvalidToken: If decryption fails
    """
    service = EncryptionService(fernet_key)
    return service.decrypt(encrypted_password)
