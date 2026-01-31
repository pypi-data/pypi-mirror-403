"""DNI (Documento Nacional de Identidad) generator for Spain.

The DNI is the national identity document for Spanish citizens.
Format: 8 digits followed by a check letter (e.g., 12345678Z).
"""

import random

from ..core import dni as dni_core


def generate_dni() -> str:
    """Generate a random valid DNI URN.

    :return: A valid DNI URN (e.g., urn:es:dni:12345678Z)
    :rtype: str
    """
    # Generate 8 random digits
    number = random.randint(0, 99999999)

    # Calculate check letter using core module
    check_letter = dni_core.calculate_check_letter(number)

    # Format as URN with 8-digit zero-padded number
    return f"urn:es:dni:{number:08d}{check_letter}"


__all__ = ["generate_dni"]
