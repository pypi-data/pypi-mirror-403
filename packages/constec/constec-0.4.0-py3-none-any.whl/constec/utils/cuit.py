"""
CUIT (Clave Única de Identificación Tributaria) utilities.

Argentine tax identification number format: XX-XXXXXXXX-X
- First 2 digits: Type (20=person, 23/24=company, 27=foreign, 30/33/34=company)
- Middle 8 digits: ID number
- Last digit: Verification digit

Usage:
    from constec.utils import normalize_cuit, validate_cuit, format_cuit

    # Normalize (remove dashes)
    normalized = normalize_cuit("20-12345678-9")  # "20123456789"

    # Validate
    is_valid = validate_cuit("20-12345678-9")  # True/False

    # Format (add dashes)
    formatted = format_cuit("20123456789")  # "20-12345678-9"
"""

import re


def normalize_cuit(cuit: str) -> str:
    """
    Normalize CUIT by removing dashes and spaces.

    Args:
        cuit: CUIT string (with or without dashes)

    Returns:
        CUIT without dashes (11 digits)

    Examples:
        >>> normalize_cuit("20-12345678-9")
        '20123456789'
        >>> normalize_cuit("20 12345678 9")
        '20123456789'
    """
    return re.sub(r'[\s\-]', '', cuit)


def format_cuit(cuit: str) -> str:
    """
    Format CUIT with dashes (XX-XXXXXXXX-X).

    Args:
        cuit: CUIT string (11 digits, with or without dashes)

    Returns:
        Formatted CUIT with dashes

    Examples:
        >>> format_cuit("20123456789")
        '20-12345678-9'
    """
    normalized = normalize_cuit(cuit)
    if len(normalized) != 11:
        return cuit  # Return as-is if invalid length
    return f"{normalized[:2]}-{normalized[2:10]}-{normalized[10]}"


def _calculate_verification_digit(cuit_base: str) -> int:
    """Calculate the CUIT verification digit using mod 11 algorithm."""
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(cuit_base, weights))
    remainder = total % 11

    if remainder == 0:
        return 0
    elif remainder == 1:
        return 9  # Special case for type 23 (women)
    else:
        return 11 - remainder


def validate_cuit(cuit: str) -> bool:
    """
    Validate a CUIT using the verification digit algorithm.

    Args:
        cuit: CUIT string (with or without dashes)

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_cuit("20-12345678-9")
        True  # (if verification digit is correct)
    """
    normalized = normalize_cuit(cuit)

    # Must be exactly 11 digits
    if not re.match(r'^\d{11}$', normalized):
        return False

    # Valid type prefixes
    valid_types = ['20', '23', '24', '27', '30', '33', '34']
    if normalized[:2] not in valid_types:
        return False

    # Verify check digit
    expected_digit = _calculate_verification_digit(normalized[:10])
    actual_digit = int(normalized[10])

    return expected_digit == actual_digit
