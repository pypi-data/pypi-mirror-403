"""NSS (Número de la Seguridad Social) extractor for Spain.

Extracts metadata from NSS URNs including province information.
"""

from typing import Any, ClassVar

from international_urns import URNExtractor

from ..core import nss as nss_core


class NSSExtractor(URNExtractor):
    """Extractor for Spanish NSS (Número de la Seguridad Social).

    Extracts the following metadata from NSS URNs:
    - province_code: The 2-digit province code
    - province_name: Name of the province (if known)
    - sequential_number: The 8-digit sequential number
    - check_digits: The 2-digit check digits
    - format: Whether it's formatted with 'slashes' or 'continuous'
    - is_special_code: Whether it's a special code (66-99) vs regular province (01-52)
    - is_valid_format: Whether the format is valid

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'nss'
    - document_value: The full NSS value

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["nss"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract NSS-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The NSS value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing NSS-specific metadata
        :rtype: dict[str, Any]
        """
        # Try pattern with slashes first
        match_slashes = nss_core.PATTERN_SLASHES.match(document_value)
        if match_slashes:
            province, sequential, check = match_slashes.groups()
            format_type = "slashes"
        else:
            # Try pattern without slashes
            match_no_slashes = nss_core.PATTERN_NO_SLASHES.match(document_value)
            if match_no_slashes:
                nss_digits = match_no_slashes.group(1)
                province = nss_digits[0:2]
                sequential = nss_digits[2:10]
                check = nss_digits[10:12]
                format_type = "continuous"
            else:
                raise ValueError(f"Invalid NSS format: {document_value}")

        # Determine if it's a special code or regular province
        province_int = int(province)
        is_special = 66 <= province_int <= 99

        # Get province name if available from core module
        default_name = "Special Code" if is_special else "Unknown"
        province_name = nss_core.PROVINCE_NAMES.get(province, default_name)

        return {
            "province_code": province,
            "province_name": province_name,
            "sequential_number": sequential,
            "check_digits": check,
            "format": format_type,
            "is_special_code": is_special,
            "is_valid_format": True,
        }


__all__ = ["NSSExtractor"]
