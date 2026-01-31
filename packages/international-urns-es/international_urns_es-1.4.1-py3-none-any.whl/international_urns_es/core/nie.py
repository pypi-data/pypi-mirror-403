"""Core constants and functions for NIE (Número de Identidad de Extranjero).

The NIE is the identification number for foreign nationals in Spain.
Format: Letter (X, Y, or Z) + 7 digits + check letter (e.g., X1234567L).

This module contains the shared business logic for NIE validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

# Check letters for NIE validation (same as DNI - modulo 23)
# The position in this string corresponds to the remainder when the full number
# (with prefix replaced) is divided by 23, yielding the correct check letter
CHECK_LETTERS: str = "TRWAGMYFPDXBNJZSQVHLCKE"

# Regular expression pattern for NIE format
# Group 1: Prefix letter (X, Y, or Z)
# Group 2: 7 digits
# Group 3: Check letter (A-Z)
PATTERN: Pattern[str] = re.compile(r"^([XYZ])(\d{7})([A-Z])$", re.IGNORECASE)

# Mapping for prefix letters to numbers for check calculation
# X = 0, Y = 1, Z = 2
PREFIX_MAP: dict[str, str] = {"X": "0", "Y": "1", "Z": "2"}

# Valid prefix letters
PREFIXES: list[str] = ["X", "Y", "Z"]

# Generation mappings for prefix letters with historical context
PREFIX_DESCRIPTIONS: dict[str, str] = {
    "X": ("Original NIE series, issued until July 15, 2008 (X = 0 for check letter calculation)"),
    "Y": (
        "Second NIE series, issued from July 16, 2008 per Orden INT/2058/2008 "
        "(Y = 1 for check letter calculation)"
    ),
    "Z": "Third NIE series, added to prevent overflow (Z = 2 for check letter calculation)",
}


def calculate_check_letter(prefix: str, number: int) -> str:
    """Calculate the NIE check letter using prefix mapping and modulo 23 algorithm.

    The check letter is determined by:
    1. Replacing the prefix letter with its corresponding digit (X→0, Y→1, Z→2)
    2. Concatenating with the 7-digit number to form an 8-digit number
    3. Taking this number modulo 23
    4. Using the result as an index into the CHECK_LETTERS string

    :param prefix: The prefix letter (X, Y, or Z)
    :type prefix: str
    :param number: The 7-digit NIE number
    :type number: int
    :return: The check letter (A-Z)
    :rtype: str
    :raises ValueError: If the prefix is invalid or number is out of range

    Example:
        >>> calculate_check_letter('X', 1234567)
        'L'
    """
    prefix = prefix.upper()
    if prefix not in PREFIX_MAP:
        raise ValueError(f"Invalid NIE prefix: {prefix}. Must be X, Y, or Z")

    if not 0 <= number <= 9999999:
        raise ValueError(f"NIE number must be between 0 and 9999999, got {number}")

    # Replace prefix with digit and concatenate with number
    full_number = int(PREFIX_MAP[prefix] + f"{number:07d}")

    return CHECK_LETTERS[full_number % 23]


__all__ = [
    "CHECK_LETTERS",
    "PATTERN",
    "PREFIX_MAP",
    "PREFIXES",
    "PREFIX_DESCRIPTIONS",
    "calculate_check_letter",
]
