"""
Password hashing utilities using bcrypt.

Usage:
    from constec.utils import hash_password, verify_password

    # Hash a password
    hashed = hash_password("my_password")

    # Verify a password
    is_valid = verify_password("my_password", hashed)  # True
"""

import bcrypt


def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password
        rounds: Cost factor (default 12, higher = slower but more secure)

    Returns:
        Bcrypt hash as string

    Example:
        >>> hashed = hash_password("secret123")
        >>> hashed.startswith("$2b$")
        True
    """
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify
        hashed: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False
