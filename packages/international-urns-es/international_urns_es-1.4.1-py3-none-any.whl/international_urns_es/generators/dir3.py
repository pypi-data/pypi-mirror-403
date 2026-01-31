"""DIR3 (Directorio Común) generator for Spain.

DIR3 codes identify administrative units and offices in the Spanish Public Administration.
Format: Exactly 9 characters - either 1 letter + 8 digits or 2 letters + 7 digits.
"""

import random

from ..core import dir3 as dir3_core


def generate_dir3() -> str:
    """Generate a random valid DIR3 URN.

    DIR3 codes are exactly 9 characters total:
    - Single-letter prefix (E, A, L, U, I, J, O) + 8 digits
    - Double-letter prefix (GE, EC, EA, LA) + 7 digits

    For L (Local Administration) codes, generates realistic structures based on
    geographic entity types with valid province/autonomous community codes.

    :return: A valid DIR3 URN (e.g., urn:es:dir3:E00010201 or urn:es:dir3:GE0001234)
    :rtype: str
    """
    # Randomly choose between single-letter and double-letter prefix (80% single, 20% double)
    if random.random() < 0.8:
        # Single-letter prefix + 8 digits
        prefix = random.choice(dir3_core.SINGLE_LETTER_PREFIXES)

        # Generate realistic L codes based on geographic entity types
        if prefix == "L":
            digits = _generate_local_admin_code()
        else:
            digits = f"{random.randint(0, 99999999):08d}"
    else:
        # Double-letter prefix + 7 digits
        prefix = random.choice(dir3_core.DOUBLE_LETTER_PREFIXES)
        digits = f"{random.randint(0, 9999999):07d}"

    code = f"{prefix}{digits}"

    # Format as URN
    return f"urn:es:dir3:{code}"


def _generate_local_admin_code() -> str:
    """Generate a realistic Local Administration (L) code.

    Generates valid structures based on geographic entity types:
    - Municipio (01): EG+PROV+CAY
    - Provincia (02): EG+0000+PROV
    - Isla (03): EG+PROV+ISLA
    - Entidad Local Menor (04): EG+PROV+LOC
    - Mancomunidad (05): EG+PROV+CMAN
    - Comarca (06): EG+CA+0+CI
    - Área Metropolitana (07): EG+PROV+LOC
    - Otras Agrupaciones (08): EG+PROV+LOC

    :return: 8-digit code for Local Administration
    :rtype: str
    """
    # Choose random geographic entity type (weighted toward common types)
    eg_choices = ["01", "02", "03", "04", "05", "06", "07", "08"]
    weights = [40, 10, 5, 10, 10, 10, 10, 5]  # Municipios most common
    eg_code = random.choices(eg_choices, weights=weights)[0]

    # Get valid province and autonomous community codes
    province_codes = list(dir3_core.PROVINCE_CODES.keys())
    ca_codes = list(dir3_core.AUTONOMOUS_COMMUNITIES.keys())

    if eg_code == "01":  # Municipio (Ayuntamiento)
        # L+EG+PROV+CAY
        prov = random.choice(province_codes)
        cay = f"{random.randint(1, 9999):04d}"
        return f"{eg_code}{prov}{cay}"

    elif eg_code == "02":  # Provincia (Diputación)
        # L+EG+0000+PROV
        prov = random.choice(province_codes)
        return f"{eg_code}0000{prov}"

    elif eg_code == "03":  # Isla (Cabildo-Consell)
        # L+EG+PROV+ISLA - only islands in Canarias (35, 38) and Baleares (07)
        island_provinces = ["07", "35", "38"]
        prov = random.choice(island_provinces)
        isla = f"{random.randint(1, 99):04d}"  # Left-padded
        return f"{eg_code}{prov}{isla}"

    elif eg_code == "04":  # Entidad Local Menor
        # L+EG+PROV+LOC
        prov = random.choice(province_codes)
        loc = f"{random.randint(1, 9999):04d}"
        return f"{eg_code}{prov}{loc}"

    elif eg_code == "05":  # Mancomunidad
        # L+EG+PROV+CMAN
        prov = random.choice(province_codes)
        cman = f"{random.randint(1, 9999):04d}"
        return f"{eg_code}{prov}{cman}"

    elif eg_code == "06":  # Comarca
        # L+EG+CA+0+CI
        ca = random.choice(ca_codes)
        ci = f"{random.randint(1, 999):03d}"
        return f"{eg_code}{ca}0{ci}"

    elif eg_code == "07":  # Área Metropolitana
        # L+EG+PROV+LOC
        prov = random.choice(province_codes)
        loc = f"{random.randint(1, 9999):04d}"
        return f"{eg_code}{prov}{loc}"

    else:  # eg_code == "08" - Otras Agrupaciones
        # L+EG+PROV+LOC
        prov = random.choice(province_codes)
        loc = f"{random.randint(1, 9999):04d}"
        return f"{eg_code}{prov}{loc}"


__all__ = ["generate_dir3"]
