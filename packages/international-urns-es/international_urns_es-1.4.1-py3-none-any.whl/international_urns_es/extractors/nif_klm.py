"""K/L/M type NIF extractor for Spain.

Extracts metadata from K/L/M type NIF URNs.
"""

from typing import Any, ClassVar

from international_urns import URNExtractor

from ..core import nif_klm as nif_klm_core


class NIFKLMExtractor(URNExtractor):
    """Extractor for Spanish K/L/M type NIF.

    Extracts the following metadata from K/L/M NIF URNs:
    - prefix: The prefix letter (K, L, or M)
    - number: The 7-digit number portion
    - check_letter: The check letter
    - category: Description of what the prefix represents
    - document_purpose: Purpose of the document
    - is_valid_format: Whether the format is valid (always True for extracted URNs)

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'nif_klm'
    - document_value: The full K/L/M NIF value (e.g., 'K1234567S')

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["nif_klm"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract K/L/M NIF-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The K/L/M NIF value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing K/L/M NIF-specific metadata
        :rtype: dict[str, Any]
        """
        # Extract K/L/M NIF components
        value_upper = document_value.upper()
        match = nif_klm_core.PATTERN.match(value_upper)

        if not match:
            raise ValueError(f"Invalid K/L/M NIF format: {document_value}")

        prefix, number_str, check_letter = match.groups()

        return {
            "prefix": prefix.upper(),
            "number": number_str,
            "check_letter": check_letter.upper(),
            "category": nif_klm_core.PREFIX_DESCRIPTIONS.get(prefix.upper(), "Unknown"),
            "document_purpose": "Tax identification for individuals without DNI or NIE",
            "is_valid_format": True,
        }


__all__ = ["NIFKLMExtractor"]
