"""Core constants and functions for DNI (Documento Nacional de Identidad).

The DNI is the national identity document for Spanish citizens.
Format: 8 digits followed by a check letter (e.g., 12345678Z).

This module contains the shared business logic for DNI validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

# Check letters for DNI validation (modulo 23)
# The position in this string corresponds to the remainder when the 8-digit number
# is divided by 23, yielding the correct check letter
CHECK_LETTERS: str = "TRWAGMYFPDXBNJZSQVHLCKE"

# Regular expression pattern for DNI format
# Group 1: 8 digits
# Group 2: Check letter (A-Z)
PATTERN: Pattern[str] = re.compile(r"^(\d{8})([A-Z])$", re.IGNORECASE)


def calculate_check_letter(number: int) -> str:
    """Calculate the DNI check letter using the modulo 23 algorithm.

    The check letter is determined by taking the DNI number modulo 23 and
    using that as an index into the CHECK_LETTERS string.

    :param number: The 8-digit DNI number
    :type number: int
    :return: The check letter (A-Z)
    :rtype: str
    :raises ValueError: If the number is not in the valid range (0-99999999)

    Example:
        >>> calculate_check_letter(12345678)
        'Z'
    """
    if not 0 <= number <= 99999999:
        raise ValueError(f"DNI number must be between 0 and 99999999, got {number}")

    return CHECK_LETTERS[number % 23]


__all__ = ["CHECK_LETTERS", "PATTERN", "calculate_check_letter"]
