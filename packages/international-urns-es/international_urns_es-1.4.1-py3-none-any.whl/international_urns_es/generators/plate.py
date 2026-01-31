"""License Plate (Matrícula) generator for Spain.

Spanish vehicle license plates. Supports current, historical, and special formats.
"""

import random

from ..core import plate as plate_core


def _generate_current_format() -> str:
    """Generate a current format plate (4 digits + 3 consonants)."""
    digits = f"{random.randint(0, 9999):04d}"
    letters = "".join(random.choices(plate_core.CONSONANTS, k=3))
    return f"{digits}{letters}"


def _generate_old_format() -> str:
    """Generate an old format plate (1-2 province letters + 4 digits + 1-2 letters)."""
    province = random.choice(plate_core.PROVINCE_CODES_LIST)
    digits = f"{random.randint(0, 9999):04d}"

    # Randomly choose 1 or 2 ending letters
    num_letters = random.randint(1, 2)
    ending = "".join(random.choices(plate_core.ALL_LETTERS, k=num_letters))

    return f"{province}{digits}{ending}"


def _generate_special_format() -> str:
    """Generate a special format plate (prefix + 4-5 digits)."""
    prefix = random.choice(plate_core.SPECIAL_PREFIXES)
    # Randomly choose 4 or 5 digits
    num_digits = random.randint(4, 5)
    digits = f"{random.randint(0, 10**num_digits - 1):0{num_digits}d}"
    return f"{prefix}{digits}"


def generate_plate() -> str:
    """Generate a random valid Spanish license plate URN.

    Generates one of three formats:
    - Current format (70%): 4 digits + 3 consonants (e.g., 1234BBC)
    - Old format (25%): 1-2 province letters + 4 digits + 1-2 letters (e.g., M1234AB)
    - Special format (5%): Special prefix + 4-5 digits (e.g., CD12345)

    :return: A valid license plate URN (e.g., urn:es:plate:1234BBC)
    :rtype: str
    """
    # Weighted random selection
    rand = random.random()

    if rand < 0.70:
        # Current format (70%)
        plate = _generate_current_format()
    elif rand < 0.95:
        # Old format (25%)
        plate = _generate_old_format()
    else:
        # Special format (5%)
        plate = _generate_special_format()

    return f"urn:es:plate:{plate}"


__all__ = ["generate_plate"]
