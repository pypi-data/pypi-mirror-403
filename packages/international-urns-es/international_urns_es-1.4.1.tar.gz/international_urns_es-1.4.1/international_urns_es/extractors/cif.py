"""CIF (Código de Identificación Fiscal) extractor for Spain.

Extracts metadata from CIF URNs including organization type detection.
"""

from typing import Any, ClassVar

from international_urns import URNExtractor

from ..core import cif as cif_core


class CIFExtractor(URNExtractor):
    """Extractor for Spanish CIF (Código de Identificación Fiscal).

    Extracts the following metadata from CIF URNs:
    - organization_type_code: The organization type letter (A-W)
    - organization_type_name: Full name of the organization type
    - organization_category: Category (legal_entity, public_entity, or religious)
    - number: The 7-digit number portion
    - check_character: The check digit/letter
    - check_format: Whether check is 'digit' or 'letter'
    - provincial_code: The province code (first 2 digits of number)
    - is_valid_format: Whether the format is valid

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'cif'
    - document_value: The full CIF value

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["cif"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract CIF-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The CIF value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing CIF-specific metadata
        :rtype: dict[str, Any]
        """
        value_upper = document_value.upper()
        match = cif_core.PATTERN.match(value_upper)

        if not match:
            raise ValueError(f"Invalid CIF format: {document_value}")

        org_type, number_str, check_char = match.groups()
        org_type = org_type.upper()
        check_char = check_char.upper()

        # Get organization type information from core module
        org_name, org_category = cif_core.ORGANIZATION_TYPES.get(org_type, ("Unknown", "unknown"))

        # Determine check character format
        if check_char.isdigit():
            check_format = "digit"
        else:
            check_format = "letter"

        # Extract provincial code (first 2 digits)
        provincial_code = number_str[:2]
        provincial_name = cif_core.PROVINCE_NAMES.get(provincial_code, "Unknown")

        return {
            "organization_type_code": org_type,
            "organization_type_name": org_name,
            "organization_category": org_category,
            "number": number_str,
            "check_character": check_char,
            "check_format": check_format,
            "provincial_code": provincial_code,
            "provincial_name": provincial_name,
            "is_valid_format": True,
        }


__all__ = ["CIFExtractor"]
