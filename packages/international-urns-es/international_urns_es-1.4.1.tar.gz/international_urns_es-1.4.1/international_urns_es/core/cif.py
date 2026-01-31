"""Core constants and functions for CIF (Código de Identificación Fiscal).

The CIF is the tax identification code for Spanish companies and organizations.
Format: Letter (organization type) + 7 digits + check digit (letter or number).
Example: A12345674, B1234567X

This module contains the shared business logic for CIF validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

from .provinces import EXTENDED_PROVINCES

# Regular expression pattern for CIF format
# Group 1: Organization type letter (A-W, excluding I, O, U which are not used)
# Group 2: 7 digits
# Group 3: Check character (letter or digit)
PATTERN: Pattern[str] = re.compile(r"^([A-HJNPQRSUVW])(\d{7})([A-J0-9])$", re.IGNORECASE)

# Check letters for CIF validation
# Used to convert the calculated check digit (0-9) to a letter
CHECK_LETTERS: str = "JABCDEFGHI"

# Organization types that must have a letter as check digit
LETTER_CHECK_TYPES: set[str] = {"N", "P", "Q", "R", "S", "W"}

# Organization types that must have a number as check digit
NUMBER_CHECK_TYPES: set[str] = {"A", "B", "E", "H"}

# Valid organization type letters
ORG_TYPES_LIST: list[str] = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "U",
    "V",
    "W",
]

# Organization type mappings
# Format: code -> (full name, category)
ORGANIZATION_TYPES: dict[str, tuple[str, str]] = {
    "A": ("Sociedad Anónima", "legal_entity"),
    "B": ("Sociedad de Responsabilidad Limitada", "legal_entity"),
    "C": ("Sociedad Colectiva", "legal_entity"),
    "D": ("Sociedad Comanditaria", "legal_entity"),
    "E": ("Comunidad de Bienes", "legal_entity"),
    "F": ("Sociedad Cooperativa", "legal_entity"),
    "G": ("Asociación", "legal_entity"),
    "H": ("Comunidad de Propietarios", "legal_entity"),
    "J": ("Sociedad Civil", "legal_entity"),
    "N": ("Entidad Extranjera", "legal_entity"),
    "P": ("Corporación Local", "public_entity"),
    "Q": ("Organismo Autónomo", "public_entity"),
    "R": ("Congregación o Institución Religiosa", "religious"),
    "S": ("Órgano de la Administración del Estado", "public_entity"),
    "U": ("Unión Temporal de Empresas", "legal_entity"),
    "V": ("Otro tipo no definido", "legal_entity"),
    "W": ("Establecimiento Permanente de Entidad No Residente", "legal_entity"),
}

# Province code mappings for CIF (extended set, codes 01-99)
# Imported from provinces module
PROVINCE_NAMES: dict[str, str] = EXTENDED_PROVINCES


def calculate_check_digit(digits: str, org_type: str) -> str:
    """Calculate the CIF check digit using the algorithm specified in Spanish law.

    The algorithm:
    1. Sum the digits in even positions (2nd, 4th, 6th)
    2. For odd positions (1st, 3rd, 5th, 7th), double each digit and sum the digits
       of the result (e.g., 7*2=14 -> 1+4=5)
    3. Add both sums together
    4. Calculate (10 - (total % 10)) % 10
    5. Convert to letter or keep as digit based on organization type

    :param digits: The 7-digit number part of the CIF
    :type digits: str
    :param org_type: The organization type letter
    :type org_type: str
    :return: The check digit as a letter or number (as string)
    :rtype: str
    :raises ValueError: If digits is not exactly 7 characters or org_type is invalid

    Example:
        >>> calculate_check_digit('1234567', 'A')
        '4'
        >>> calculate_check_digit('1234567', 'N')
        'E'
    """
    if len(digits) != 7 or not digits.isdigit():
        raise ValueError(f"Digits must be exactly 7 numeric characters, got '{digits}'")

    org_type = org_type.upper()
    if org_type not in ORG_TYPES_LIST:
        raise ValueError(f"Invalid organization type: {org_type}")

    # Sum of digits in even positions (2nd, 4th, 6th) - indices 1, 3, 5
    even_sum = sum(int(digits[i]) for i in range(1, 7, 2))

    # For odd positions (1st, 3rd, 5th, 7th) - indices 0, 2, 4, 6
    # Double each digit and sum the digits of the result
    odd_sum = 0
    for i in range(0, 7, 2):
        doubled = int(digits[i]) * 2
        # Sum the digits of the doubled value (e.g., 14 -> 1 + 4 = 5)
        odd_sum += doubled // 10 + doubled % 10

    # Total sum
    total = even_sum + odd_sum

    # Calculate check digit
    check_digit = (10 - (total % 10)) % 10

    # Return as letter or number based on organization type
    if org_type in LETTER_CHECK_TYPES:
        # Must return a letter
        return CHECK_LETTERS[check_digit]
    elif org_type in NUMBER_CHECK_TYPES:
        # Must return a number
        return str(check_digit)
    else:
        # For other types, return letter (most common practice)
        return CHECK_LETTERS[check_digit]


__all__ = [
    "PATTERN",
    "CHECK_LETTERS",
    "LETTER_CHECK_TYPES",
    "NUMBER_CHECK_TYPES",
    "ORG_TYPES_LIST",
    "ORGANIZATION_TYPES",
    "PROVINCE_NAMES",
    "calculate_check_digit",
]
