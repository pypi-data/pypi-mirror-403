"""DIR3 (Directorio Común de unidades y oficinas) validator for Spain.

DIR3 is the Common Directory of units and offices of the Spanish Public Administration.
Format: 9 character alphanumeric code.
Examples: E00010201, A01000001, L01000001, GE0000001, O00000001
"""

from typing import ClassVar

from international_urns import URNValidator

from ..core import dir3 as dir3_core


class DIR3Validator(URNValidator):
    """Validator for Spanish DIR3 codes.

    DIR3 codes identify administrative units and offices in the Spanish
    Public Administration. They consist of exactly 9 alphanumeric characters.

    Valid format: urn:es:dir3:E00010201

    The code structure:
    - First 1-2 characters: Administration level identifier
      E=State, A=Autonomous, L=Local, U=Universities, I=Institutions,
      J=Justice, O=Offices, GE=Economic Units, EC=Collaborating Entities,
      EA=State (no RCP), LA=Local Public Entities
    - Remaining 7-8 digits: Identifier (structure varies by type)

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["dir3"]  # type: ignore[misc]

    def validate(self, urn: str) -> str:
        """Validate a Spanish DIR3 URN.

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

        # Validate DIR3 format
        self._validate_dir3(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_dir3(self, dir3: str) -> None:
        """Validate DIR3 code format.

        :param dir3: The DIR3 value to validate
        :type dir3: str
        :raises ValueError: If the DIR3 code is invalid
        """
        # Convert to uppercase for validation
        dir3 = dir3.upper()

        # Check length (must be exactly 9)
        if len(dir3) != 9:
            raise ValueError(f"Invalid DIR3 length: {dir3}. Expected exactly 9 characters")

        # Try single letter prefix pattern first
        match_single = dir3_core.PATTERN_SINGLE.match(dir3)
        if match_single:
            prefix, unit_code = match_single.groups()
            # Additional validation for L codes
            if prefix == "L":
                self._validate_local_admin_structure(unit_code)
            return

        # Try double letter prefix pattern
        match_double = dir3_core.PATTERN_DOUBLE.match(dir3)
        if match_double:
            return

        # If neither pattern matches, provide detailed error
        raise ValueError(
            f"Invalid DIR3 format: {dir3}. Expected format: "
            "E/A/L/U/I/J/O + 8 digits, or GE/EC/EA/LA + 7 digits"
        )

    def _validate_local_admin_structure(self, unit_code: str) -> None:
        """Validate the structure of Local Administration (L) codes.

        :param unit_code: The 8-digit unit code from L codes
        :type unit_code: str
        :raises ValueError: If the L code structure is invalid
        """
        if len(unit_code) != 8:
            return  # Not enough data to validate structure

        eg_code = unit_code[0:2]

        # Validate geographic entity type code exists
        if eg_code not in dir3_core.GEOGRAPHIC_ENTITIES:
            raise ValueError(
                f"Invalid geographic entity code '{eg_code}' in Local Administration code. "
                f"Expected one of: {', '.join(dir3_core.GEOGRAPHIC_ENTITIES.keys())}"
            )

        # Validate structure based on entity type
        if eg_code == "02":  # Provincia (Diputación)
            # L+EG+0000+PROV - middle 4 digits must be 0000
            middle_part = unit_code[2:6]
            if middle_part != "0000":
                raise ValueError(
                    f"Invalid Diputación code structure. "
                    f"Expected L02+0000+PROV, got L02{middle_part}XX"
                )
            prov_code = unit_code[6:8]
            if prov_code not in dir3_core.PROVINCE_CODES:
                raise ValueError(
                    f"Invalid province code '{prov_code}' in Diputación code. "
                    f"Expected valid province code (01-52)"
                )

        elif eg_code == "06":  # Comarca
            # L+EG+CA+0+CI - position 4 (index 4) must be 0
            if unit_code[4] != "0":
                raise ValueError("Invalid Comarca code structure. Expected L06+CA+0+CI format")
            ca_code = unit_code[2:4]
            if ca_code not in dir3_core.AUTONOMOUS_COMMUNITIES:
                raise ValueError(
                    f"Invalid autonomous community code '{ca_code}' in Comarca code. "
                    f"Expected valid autonomous community code (01-19)"
                )

        elif eg_code in ["01", "03", "04", "05", "07", "08"]:
            # These types use L+EG+PROV+XXXX format
            prov_code = unit_code[2:4]
            if prov_code not in dir3_core.PROVINCE_CODES:
                raise ValueError(
                    f"Invalid province code '{prov_code}' in "
                    f"{dir3_core.GEOGRAPHIC_ENTITIES[eg_code]} code. "
                    f"Expected valid province code (01-52)"
                )


__all__ = ["DIR3Validator"]
