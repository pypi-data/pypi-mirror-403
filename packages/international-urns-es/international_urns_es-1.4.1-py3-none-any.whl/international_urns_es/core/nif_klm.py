"""Core constants and functions for K/L/M type NIFs.

Special NIF formats for individuals who don't have DNI or NIE:
- K: Spanish residents under 14 years old (no DNI required)
- L: Spanish nationals resident abroad (no DNI required)
- M: Foreign nationals without NIE

Format: Letter (K, L, or M) + 7 digits + check letter (e.g., K1234567S).

This module contains the shared business logic for K/L/M NIF validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

# Check letters for K/L/M NIF validation (same as DNI - modulo 23)
# The position in this string corresponds to the remainder when the 7-digit number
# is divided by 23, yielding the correct check letter
CHECK_LETTERS: str = "TRWAGMYFPDXBNJZSQVHLCKE"

# Regular expression pattern for K/L/M NIF format
# Group 1: Prefix letter (K, L, or M)
# Group 2: 7 digits
# Group 3: Check letter (A-Z)
PATTERN: Pattern[str] = re.compile(r"^([KLM])(\d{7})([A-Z])$", re.IGNORECASE)

# Valid prefix letters
PREFIXES: list[str] = ["K", "L", "M"]

# Generation mappings for prefix letters with descriptions
PREFIX_DESCRIPTIONS: dict[str, str] = {
    "K": "Spanish residents under 14 years old (not required to possess DNI)",
    "L": "Spanish nationals resident abroad (not required to possess DNI)",
    "M": (
        "Foreign nationals without NIE, either temporarily or definitively "
        "(not obliged to have NIE)"
    ),
}


def calculate_check_letter(number: int) -> str:
    """Calculate the K/L/M NIF check letter using the modulo 23 algorithm.

    Unlike NIE, the prefix letter is not replaced with a digit.
    The check letter is determined by taking the 7-digit number modulo 23 and
    using that as an index into the CHECK_LETTERS string.

    :param number: The 7-digit NIF number
    :type number: int
    :return: The check letter (A-Z)
    :rtype: str
    :raises ValueError: If the number is not in the valid range (0-9999999)

    Example:
        >>> calculate_check_letter(1234567)
        'S'
    """
    if not 0 <= number <= 9999999:
        raise ValueError(f"K/L/M NIF number must be between 0 and 9999999, got {number}")

    return CHECK_LETTERS[number % 23]


__all__ = [
    "CHECK_LETTERS",
    "PATTERN",
    "PREFIXES",
    "PREFIX_DESCRIPTIONS",
    "calculate_check_letter",
]
