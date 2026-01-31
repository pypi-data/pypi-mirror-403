"""NIE (Número de Identidad de Extranjero) generator for Spain.

The NIE is the identification number for foreign nationals in Spain.
Format: Letter (X, Y, or Z) + 7 digits + check letter (e.g., X1234567L).
"""

import random

from ..core import nie as nie_core


def generate_nie() -> str:
    """Generate a random valid NIE URN.

    :return: A valid NIE URN (e.g., urn:es:nie:X1234567L)
    :rtype: str
    """
    # Select random prefix
    prefix = random.choice(nie_core.PREFIXES)

    # Generate 7 random digits
    number = random.randint(0, 9999999)

    # Calculate check letter using core module
    check_letter = nie_core.calculate_check_letter(prefix, number)

    # Format as URN
    return f"urn:es:nie:{prefix}{number:07d}{check_letter}"


__all__ = ["generate_nie"]
