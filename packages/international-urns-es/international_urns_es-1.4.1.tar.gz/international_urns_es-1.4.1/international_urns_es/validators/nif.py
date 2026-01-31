"""NIF (Número de Identificación Fiscal) validator for Spain.

The NIF is the tax identification number for individuals in Spain.
For individuals, it can be either a DNI, NIE, or K/L/M format.
Format: 12345678Z (DNI), X1234567L (NIE), or K1234567S (K/L/M).
"""

from contextlib import suppress
from typing import ClassVar

from international_urns import URNValidator

from international_urns_es.validators.cif import CIFValidator
from international_urns_es.validators.dni import DNIValidator
from international_urns_es.validators.nie import NIEValidator
from international_urns_es.validators.nif_klm import NIFKLMValidator


class NIFValidator(URNValidator):
    """Validator for Spanish NIF (Número de Identificación Fiscal).

    The NIF for individuals accepts DNI, NIE, and K/L/M formats:
    - DNI format: 8 digits + check letter
    - NIE format: Letter (X, Y, Z) + 7 digits + check letter
    - K/L/M format: Letter (K, L, M) + 7 digits + check letter

    The NIF for legal entities accepts the CIF format.

    Valid formats:
    - urn:es:nif:12345678Z (DNI format)
    - urn:es:nif:X1234567L (NIE format)
    - urn:es:nif:K1234567S (K/L/M format)
    - urn:es:nif:A12345674 (CIF format for legal entities)

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["nif"]  # type: ignore[misc]

    def validate(self, urn: str) -> str:
        """Validate a Spanish NIF URN.

        :param urn: The URN to validate
        :type urn: str
        :return: The validated URN
        :rtype: str
        :raises ValueError: If the URN is invalid
        """
        # Parse URN
        parts = urn.split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid URN format: {urn}")

        scheme, country, doc_type, value = parts

        if scheme.lower() != "urn":
            raise ValueError(f"Invalid URN scheme: {scheme}")

        if country.lower() != self.country_code:
            raise ValueError(f"Invalid country code: {country}")

        if doc_type.lower() not in self.document_types:
            raise ValueError(f"Invalid document type: {doc_type}")

        # Validate NIF format (DNI or NIE)
        self._validate_nif(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_nif(self, nif: str) -> None:
        """Validate NIF number and check letter.

        Accepts DNI, NIE, K/L/M, and CIF formats.

        :param nif: The NIF value to validate
        :type nif: str
        :raises ValueError: If the NIF is invalid
        """
        # Convert to uppercase for validation
        nif = nif.upper()

        # Try DNI format first
        with suppress(ValueError):
            DNIValidator().validate(f"urn:es:dni:{nif}")
            return

        # Try NIE format
        with suppress(ValueError):
            NIEValidator().validate(f"urn:es:nie:{nif}")
            return

        # Try K/L/M format
        with suppress(ValueError):
            NIFKLMValidator().validate(f"urn:es:nif_klm:{nif}")
            return

        # Try CIF format
        with suppress(ValueError):
            CIFValidator().validate(f"urn:es:cif:{nif}")
            return

        raise ValueError(f"Invalid NIF format: {nif}. Expected DNI, NIE, K/L/M or CIF format.")


__all__ = ["NIFValidator"]
