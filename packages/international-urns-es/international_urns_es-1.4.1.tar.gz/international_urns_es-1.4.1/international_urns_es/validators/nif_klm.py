"""K/L/M type NIF validator for Spain.

Special NIF formats for individuals who don't have DNI or NIE:
- K: Spanish residents under 14 years old
- L: Spanish nationals resident abroad
- M: Foreign nationals without NIE

Format: Letter (K, L, or M) + 7 digits + check letter (e.g., K1234567S).
"""

from typing import ClassVar

from international_urns import URNValidator

from ..core import nif_klm as nif_klm_core


class NIFKLMValidator(URNValidator):
    """Validator for Spanish K/L/M type NIF.

    The K/L/M NIF consists of a prefix letter (K, L, or M), 7 digits, and a check letter
    calculated using the modulo 23 algorithm (without prefix replacement).

    Valid format: urn:es:nif_klm:K1234567S

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["nif_klm"]  # type: ignore[misc]

    def validate(self, urn: str) -> str:
        """Validate a Spanish K/L/M type NIF URN.

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

        # Validate K/L/M NIF format and check letter
        self._validate_nif_klm(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_nif_klm(self, nif_klm: str) -> None:
        """Validate K/L/M NIF number and check letter.

        :param nif_klm: The K/L/M NIF value to validate
        :type nif_klm: str
        :raises ValueError: If the K/L/M NIF is invalid
        """
        # Convert to uppercase for validation
        nif_klm = nif_klm.upper()

        match = nif_klm_core.PATTERN.match(nif_klm)
        if not match:
            raise ValueError(
                f"Invalid K/L/M NIF format: {nif_klm}. "
                "Expected letter (K, L, or M) + 7 digits + check letter"
            )

        prefix, number_str, letter = match.groups()

        # Calculate expected check letter using core module
        expected_letter = nif_klm_core.calculate_check_letter(int(number_str))

        if letter != expected_letter:
            raise ValueError(
                f"Invalid K/L/M NIF check letter: {nif_klm}. "
                f"Expected {expected_letter}, got {letter}"
            )


__all__ = ["NIFKLMValidator"]
