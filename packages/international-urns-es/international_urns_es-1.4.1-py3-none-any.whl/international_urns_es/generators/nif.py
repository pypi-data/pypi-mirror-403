"""NIF (Número de Identificación Fiscal) generator for Spain.

The NIF is the tax identification number in Spain.
It accepts all DNI, NIE, K/L/M, and CIF formats.
"""

import random

from international_urns_es.generators.cif import generate_cif
from international_urns_es.generators.dni import generate_dni
from international_urns_es.generators.nie import generate_nie
from international_urns_es.generators.nif_klm import generate_nif_klm


def generate_nif() -> str:
    """Generate a random valid NIF URN.

    The NIF can be either a DNI, NIE, K/L/M or CIF format. This generator randomly
    selects one of the formats.

    :return: A valid NIF URN (e.g., urn:es:nif:12345678Z, urn:es:nif:X1234567L,
             or urn:es:nif:K1234567S)
    :rtype: str
    """
    # Randomly choose between DNI, NIE, K/L/M or CIF format
    nif_type: str = random.choice(["dni", "nie", "nif_klm", "cif"])
    if nif_type == "cif":
        urn: str = generate_cif()
    elif nif_type == "dni":
        urn = generate_dni()
    elif nif_type == "nie":
        urn = generate_nie()
    else:
        urn = generate_nif_klm()
    return urn.replace(f":{nif_type}:", ":nif:")


__all__ = ["generate_nif"]
