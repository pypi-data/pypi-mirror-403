"""Core constants and functions for NSS (Número de la Seguridad Social).

The NSS is the Social Security Number used in Spain.
Format: 12 digits in the pattern XX/XXXXXXXXXX/XX or as a continuous 12-digit number.
Example: 281234567840 or 28/12345678/40

Structure:
- First 2 digits: Province code (01-52 or special codes 66-99)
- Next 8 digits: Sequential number
- Last 2 digits: Check digits

This module contains the shared business logic for NSS validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

from .provinces import STANDARD_PROVINCES

# Regular expression pattern for NSS with slashes
# Group 1: 2-digit province code
# Group 2: 8-digit sequential number
# Group 3: 2-digit check digits
PATTERN_SLASHES: Pattern[str] = re.compile(r"^(\d{2})/(\d{8})/(\d{2})$")

# Regular expression pattern for NSS without slashes (continuous 12 digits)
PATTERN_NO_SLASHES: Pattern[str] = re.compile(r"^(\d{12})$")

# Valid province codes: 01-52 (standard provinces) and 66-99 (special codes)
VALID_PROVINCES: list[int] = list(range(1, 53)) + list(range(66, 100))

# Province code mappings (codes 01-52)
# Imported from provinces module
PROVINCE_NAMES: dict[str, str] = STANDARD_PROVINCES


def calculate_check_digits(base_number: int) -> int:
    """Calculate NSS check digits using modulo 97.

    The check digits are calculated by taking the base number (province + sequential)
    modulo 97. This is a standard checksum algorithm used for the Spanish NSS.

    :param base_number: The first 10 digits (province + sequential number)
    :type base_number: int
    :return: The 2-digit check digits (0-96)
    :rtype: int
    :raises ValueError: If base_number is out of valid range

    Example:
        >>> calculate_check_digits(2812345678)
        40
    """
    if not 0 <= base_number <= 9999999999:
        raise ValueError(f"Base number must be between 0 and 9999999999, got {base_number}")

    return base_number % 97


__all__ = [
    "PATTERN_SLASHES",
    "PATTERN_NO_SLASHES",
    "VALID_PROVINCES",
    "PROVINCE_NAMES",
    "calculate_check_digits",
]
