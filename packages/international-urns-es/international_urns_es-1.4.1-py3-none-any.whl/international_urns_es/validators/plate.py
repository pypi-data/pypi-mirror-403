"""Spanish vehicle license plate validator.

Spanish license plates have evolved through different formats:
- Current format (since 2000): 4 digits + 3 letters (e.g., 1234ABC)
- Old format (1971-2000): 1-2 province letters + 4 digits + 1-2 letters (e.g., M1234AB)
"""

from typing import ClassVar

from international_urns import URNValidator

from ..core import plate as plate_core


class PlateValidator(URNValidator):
    """Validator for Spanish vehicle license plates.

    Supports both current and historical license plate formats:

    Current format (since 2000):
    - 4 digits followed by 3 consonants (excluding vowels and Ñ, Q)
    - Example: 1234BBC

    Old format (1971-2000):
    - 1-2 province letters + 4 digits + 1-2 letters
    - Examples: M1234AB, MA1234B

    Valid formats:
    - urn:es:plate:1234BBC (current)
    - urn:es:plate:M1234AB (old)

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["plate", "matricula"]  # type: ignore[misc]

    def validate(self, urn: str) -> str:
        """Validate a Spanish license plate URN.

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

        # Validate plate format
        self._validate_plate(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_plate(self, plate: str) -> None:
        """Validate license plate format.

        :param plate: The license plate value to validate
        :type plate: str
        :raises ValueError: If the license plate is invalid
        """
        # Remove spaces and hyphens, convert to uppercase
        plate = plate.replace(" ", "").replace("-", "").upper()

        # Try current format
        if plate_core.PATTERN_CURRENT.match(plate):
            return

        # Try old format
        old_match = plate_core.PATTERN_OLD.match(plate)
        if old_match:
            province = old_match.group(1)
            if province in plate_core.PROVINCE_CODES_SET:
                return
            raise ValueError(f"Invalid province code in old format plate: {province}")

        # Try special formats
        if plate_core.PATTERN_SPECIAL.match(plate):
            return

        raise ValueError(
            f"Invalid license plate format: {plate}. "
            "Expected current format (1234ABC), old format (M1234AB), "
            "or special format (CD1234)"
        )


__all__ = ["PlateValidator"]
