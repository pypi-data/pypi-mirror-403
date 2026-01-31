"""CIF (Código de Identificación Fiscal) generator for Spain.

The CIF is the tax identification code for Spanish companies and organizations.
Format: Letter (organization type) + 7 digits + check digit (letter or number).
"""

import random

from ..core import cif as cif_core


def generate_cif() -> str:
    """Generate a random valid CIF URN.

    :return: A valid CIF URN (e.g., urn:es:cif:A12345674 or urn:es:cif:N1234567J)
    :rtype: str
    """
    # Select random organization type
    org_type = random.choice(cif_core.ORG_TYPES_LIST)

    # Generate 7 random digits
    digits = f"{random.randint(0, 9999999):07d}"

    # Calculate check digit using core module
    check_digit = cif_core.calculate_check_digit(digits, org_type)

    # Format as URN
    return f"urn:es:cif:{org_type}{digits}{check_digit}"


__all__ = ["generate_cif"]
