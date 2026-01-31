"""Spanish vehicle license plate extractor.

Extracts metadata from license plate URNs including format detection.
"""

from typing import Any, ClassVar

from international_urns import URNExtractor

from ..core import plate as plate_core


class PlateExtractor(URNExtractor):
    """Extractor for Spanish vehicle license plates.

    Extracts the following metadata from license plate URNs:
    - plate_format: Format type ('current', 'old', or 'special')
    - digits: The numeric portion
    - letters: The letter portion
    - province_code: Province code (only for old format)
    - province_name: Province name (only for old format, if known)
    - special_type: Type of special plate (only for special format)
    - special_type_description: Description of special plate type
    - is_valid_format: Whether the format is valid

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'plate' or 'matricula'
    - document_value: The full plate value

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["plate", "matricula"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract license plate-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The plate value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing plate-specific metadata
        :rtype: dict[str, Any]
        """
        # Remove spaces and hyphens, convert to uppercase
        plate = document_value.replace(" ", "").replace("-", "").upper()

        # Try current format
        current_match = plate_core.PATTERN_CURRENT.match(plate)
        if current_match:
            digits, letters = current_match.groups()
            return {
                "plate_format": "current",
                "digits": digits,
                "letters": letters.upper(),
                "is_valid_format": True,
            }

        # Try old format
        old_match = plate_core.PATTERN_OLD.match(plate)
        if old_match:
            province_code, digits, letters = old_match.groups()
            province_code = province_code.upper()
            province_name = plate_core.PROVINCE_NAMES.get(province_code, "Unknown")
            return {
                "plate_format": "old",
                "province_code": province_code,
                "province_name": province_name,
                "digits": digits,
                "letters": letters.upper(),
                "is_valid_format": True,
            }

        # Try special formats
        special_match = plate_core.PATTERN_SPECIAL.match(plate)
        if special_match:
            special_type, digits = special_match.groups()
            special_type = special_type.upper()
            special_description = plate_core.SPECIAL_TYPES.get(special_type, "Unknown special type")
            return {
                "plate_format": "special",
                "special_type": special_type,
                "special_type_description": special_description,
                "digits": digits,
                "is_valid_format": True,
            }

        raise ValueError(f"Invalid license plate format: {document_value}")


__all__ = ["PlateExtractor"]
