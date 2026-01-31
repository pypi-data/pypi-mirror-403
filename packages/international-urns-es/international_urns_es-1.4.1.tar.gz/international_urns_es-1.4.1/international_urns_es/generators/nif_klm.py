"""K/L/M type NIF generator for Spain.

Special NIF formats for individuals who don't have DNI or NIE:
- K: Spanish residents under 14 years old
- L: Spanish nationals resident abroad
- M: Foreign nationals without NIE

Format: Letter (K, L, or M) + 7 digits + check letter (e.g., K1234567S).
"""

import random

from ..core import nif_klm as nif_klm_core


def generate_nif_klm() -> str:
    """Generate a random valid K/L/M type NIF URN.

    :return: A valid K/L/M NIF URN (e.g., urn:es:nif_klm:K1234567S)
    :rtype: str
    """
    # Select random prefix
    prefix = random.choice(nif_klm_core.PREFIXES)

    # Generate 7 random digits
    number = random.randint(0, 9999999)

    # Calculate check letter using core module
    check_letter = nif_klm_core.calculate_check_letter(number)

    # Format as URN
    return f"urn:es:nif_klm:{prefix}{number:07d}{check_letter}"


__all__ = ["generate_nif_klm"]
