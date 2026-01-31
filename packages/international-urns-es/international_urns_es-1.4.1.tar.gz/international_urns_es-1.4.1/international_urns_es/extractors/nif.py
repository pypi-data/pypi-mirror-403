"""NIF (Número de Identificación Fiscal) extractor for Spain.

Extracts metadata from NIF URNs.
"""

from contextlib import suppress
from typing import Any, ClassVar

from international_urns import URNExtractor

from international_urns_es.extractors.cif import CIFExtractor
from international_urns_es.extractors.dni import DNIExtractor
from international_urns_es.extractors.nie import NIEExtractor
from international_urns_es.extractors.nif_klm import NIFKLMExtractor


class NIFExtractor(URNExtractor):
    """Extractor for Spanish NIF (Número de Identificación Fiscal).

    Extracts the following metadata from NIF URNs:
    - format_type: Either 'dni', 'nie', 'nif_klm' or 'cif'
    - all other relevant fields extracted by the format-specific extractor

    Base fields (automatically included):
    - country_code: 'es'
    - document_type: 'nif'
    - document_value: The full NIF value

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["nif"]  # type: ignore[misc]

    def _extract_metadata(
        self,
        country_code: str,
        document_type: str,
        document_value: str,
        nss_parts: list[str],
    ) -> dict[str, Any]:
        """Extract NIF-specific metadata.

        :param country_code: The country code from the URN
        :type country_code: str
        :param document_type: The document type from the URN
        :type document_type: str
        :param document_value: The NIF value to extract from
        :type document_value: str
        :param nss_parts: The tokenized NSS parts
        :type nss_parts: list[str]
        :return: Dictionary containing NIF-specific metadata
        :rtype: dict[str, Any]
        """
        # Try DNI format
        with suppress(ValueError):
            dni_metadata: dict[str, Any] = DNIExtractor().extract(
                f"urn:{country_code}:dni:{document_value}"
            )
            dni_metadata["format_type"] = dni_metadata["document_type"]
            dni_metadata["document_type"] = "nif"
            return dni_metadata

        # Try NIE format
        with suppress(ValueError):
            nie_metadata: dict[str, Any] = NIEExtractor().extract(
                f"urn:{country_code}:nie:{document_value}"
            )
            nie_metadata["format_type"] = nie_metadata["document_type"]
            nie_metadata["document_type"] = "nif"
            return nie_metadata

        # Try K/L/M format
        with suppress(ValueError):
            nif_klm_metadata: dict[str, Any] = NIFKLMExtractor().extract(
                f"urn:{country_code}:nif_klm:{document_value}"
            )
            nif_klm_metadata["format_type"] = nif_klm_metadata["document_type"]
            nif_klm_metadata["document_type"] = "nif"
            return nif_klm_metadata

        # Try CIF format
        with suppress(ValueError):
            cif_metadata: dict[str, Any] = CIFExtractor().extract(
                f"urn:{country_code}:cif:{document_value}"
            )
            cif_metadata["format_type"] = cif_metadata["document_type"]
            cif_metadata["document_type"] = "nif"
            return cif_metadata

        raise ValueError(f"Invalid NIF format: {document_value}")


__all__ = ["NIFExtractor"]
