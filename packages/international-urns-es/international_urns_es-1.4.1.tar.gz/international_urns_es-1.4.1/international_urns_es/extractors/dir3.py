"""DIR3 (Directorio Común) extractor for Spain.

Extracts metadata from DIR3 URNs including administration level detection.
"""

from typing import Any, ClassVar

from international_urns import URNExtractor

from ..core import dir3 as dir3_core


class DIR3Extractor(URNExtractor):
    """Extractor for Spanish DIR3 (Directorio Común) codes.

    Extracts the following metadata from DIR3 URNs:
    - administration_level_code: The administration level prefix
      (E, A, L, U, I, J, O, GE, EC, EA, LA)
    - administration_level_name: Full name of the administration level
    - unit_code: The numeric identifier (7-8 digits depending on prefix)
    - For A codes: autonomous_community_code and autonomous_community_name
    - For L codes: geographic_entity_code, geographic_entity_name, and detailed structure:
      - For EG=01 (Municipio): province_code, province_name, municipality_code
      - For EG=02 (Provincia): province_code, province_name
      - For EG=03 (Isla): province_code, province_name, island_code
      - For EG=04 (Entidad Local Menor): province_code, province_name, locality_code
      - For EG=05 (Mancomunidad): province_code, province_name, commonwealth_code
      - For EG=06 (Comarca): autonomous_community_code, autonomous_community_name, comarca_code
      - For EG=07 (Área Metropolitana): province_code, province_name, locality_code
      - For EG=08 (Otras Agrupaciones): province_code, province_name, locality_code
    - For U codes: university_siiu_code (3-digit SIIU code assigned by Ministry of Education)
    - For LA codes: entity_number (7-digit entity identifier)
    - is_valid_format: Whether the format is valid

    Note: Extracted codes have left-padding zeros removed.

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'dir3'
    - document_value: The full DIR3 value

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["dir3"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract DIR3-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The DIR3 value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing DIR3-specific metadata
        :rtype: dict[str, Any]
        """
        value_upper = document_value.upper()

        # Try single-letter prefix first
        match_single = dir3_core.PATTERN_SINGLE.match(value_upper)
        if match_single:
            prefix, unit_code = match_single.groups()
            prefix = prefix.upper()
            admin_name = dir3_core.ADMIN_LEVELS.get(prefix, "Unknown")

            result: dict[str, Any] = {
                "administration_level_code": prefix,
                "administration_level_name": admin_name,
                "unit_code": unit_code,
                "is_valid_format": True,
            }

            # Extract additional info for Autonomous Administration (A)
            if prefix == "A" and len(unit_code) >= 2:
                ca_code = unit_code[0:2]
                ca_name = dir3_core.AUTONOMOUS_COMMUNITIES.get(ca_code, "Unknown")
                result["autonomous_community_code"] = ca_code
                result["autonomous_community_name"] = ca_name

            # Extract additional info for Local Administration (L)
            elif prefix == "L" and len(unit_code) >= 2:
                eg_code = unit_code[0:2]
                eg_name = dir3_core.GEOGRAPHIC_ENTITIES.get(eg_code, "Unknown")
                result["geographic_entity_code"] = eg_code
                result["geographic_entity_name"] = eg_name

                # Extract detailed structure based on entity type
                # Remove left-padding zeros when extracting
                if len(unit_code) == 8:
                    if eg_code == "01":  # Municipio (Ayuntamiento)
                        # L+EG+PROV+CAY (PROV=2, CAY=4)
                        prov_code = unit_code[2:4]
                        municipality_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["municipality_code"] = municipality_code

                    elif eg_code == "02":  # Provincia (Diputación)
                        # L+EG+0000+PROV (PROV=2)
                        prov_code = unit_code[6:8]
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")

                    elif eg_code == "03":  # Isla (Cabildo-Consell)
                        # L+EG+PROV+ISLA (PROV=2, ISLA=4)
                        prov_code = unit_code[2:4]
                        island_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["island_code"] = island_code

                    elif eg_code == "04":  # Entidad Local Menor
                        # L+EG+PROV+LOC (PROV=2, LOC=4)
                        prov_code = unit_code[2:4]
                        locality_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["locality_code"] = locality_code

                    elif eg_code == "05":  # Mancomunidad
                        # L+EG+PROV+CMAN (PROV=2, CMAN=4)
                        prov_code = unit_code[2:4]
                        commonwealth_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["commonwealth_code"] = commonwealth_code

                    elif eg_code == "06":  # Comarca
                        # L+EG+CA+0+CI (CA=2, 0, CI=3)
                        ca_code = unit_code[2:4]
                        comarca_code = unit_code[5:8].lstrip("0") or "0"
                        result["autonomous_community_code"] = ca_code
                        result["autonomous_community_name"] = dir3_core.AUTONOMOUS_COMMUNITIES.get(
                            ca_code, "Unknown"
                        )
                        result["comarca_code"] = comarca_code

                    elif eg_code == "07":  # Área Metropolitana
                        # L+EG+PROV+LOC (PROV=2, LOC=4)
                        prov_code = unit_code[2:4]
                        locality_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["locality_code"] = locality_code

                    elif eg_code == "08":  # Otras Agrupaciones
                        # L+EG+PROV+LOC (PROV=2, LOC=4)
                        prov_code = unit_code[2:4]
                        locality_code = unit_code[4:8].lstrip("0") or "0"
                        result["province_code"] = prov_code
                        result["province_name"] = dir3_core.PROVINCE_CODES.get(prov_code, "Unknown")
                        result["locality_code"] = locality_code

            # Extract additional info for Universities (U)
            elif prefix == "U" and len(unit_code) >= 3:
                siiu_code = unit_code[0:3]
                result["university_siiu_code"] = siiu_code

            return result

        # Try double-letter prefix
        match_double = dir3_core.PATTERN_DOUBLE.match(value_upper)
        if match_double:
            prefix, unit_code = match_double.groups()
            prefix = prefix.upper()
            admin_name = dir3_core.ADMIN_LEVELS.get(prefix, "Unknown")

            result = {
                "administration_level_code": prefix,
                "administration_level_name": admin_name,
                "unit_code": unit_code,
                "is_valid_format": True,
            }

            # Extract additional info for LA (Local Public Entities)
            if prefix == "LA":
                # For LA codes, simply extract the number
                result["entity_number"] = unit_code.lstrip("0") or "0"

            return result

        raise ValueError(f"Invalid DIR3 format: {document_value}")


__all__ = ["DIR3Extractor"]
