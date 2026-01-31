"""CIF (Código de Identificación Fiscal) validator for Spain.

The CIF is the tax identification code for Spanish companies and organizations.
Format: Letter (organization type) + 7 digits + check digit (letter or number).
Example: A12345674, B1234567X
"""

from typing import ClassVar

from international_urns import URNValidator

from ..core import cif as cif_core


class CIFValidator(URNValidator):
    """Validator for Spanish CIF (Código de Identificación Fiscal).

    The CIF consists of:
    - 1 letter indicating organization type (A-W, except I, O, U)
    - 7 digits
    - 1 check character (letter or digit depending on organization type)

    Valid format: urn:es:cif:A12345674 or urn:es:cif:B1234567X

    Organization type letters:
    - A: Sociedades Anónimas
    - B: Sociedades de Responsabilidad Limitada
    - C: Sociedades Colectivas
    - D: Sociedades Comanditarias
    - E: Comunidades de Bienes
    - F: Sociedades Cooperativas
    - G: Asociaciones
    - H: Comunidades de Propietarios
    - J: Sociedades Civiles
    - N: Entidades Extranjeras
    - P: Corporaciones Locales
    - Q: Organismos Autónomos
    - R: Congregaciones e Instituciones Religiosas
    - S: Órganos de la Administración del Estado
    - U: Uniones Temporales de Empresas
    - V: Otros tipos no definidos
    - W: Establecimientos permanentes de entidades no residentes

    :cvar country_code: ISO 3166-1 Alpha-2 code for Spain
    :cvar document_types: List of supported document type identifiers
    """

    country_code: ClassVar[str] = "es"  # type: ignore[misc]
    document_types: ClassVar[list[str]] = ["cif"]  # type: ignore[misc]

    def validate(self, urn: str) -> str:
        """Validate a Spanish CIF URN.

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

        # Validate CIF format and check digit
        self._validate_cif(value)

        # Return normalized URN (lowercase scheme, country, and doc_type)
        return f"urn:{country.lower()}:{doc_type.lower()}:{value}"

    def _validate_cif(self, cif: str) -> None:
        """Validate CIF format and check digit.

        :param cif: The CIF value to validate
        :type cif: str
        :raises ValueError: If the CIF is invalid
        """
        # Convert to uppercase for validation
        cif = cif.upper()

        match = cif_core.PATTERN.match(cif)
        if not match:
            raise ValueError(
                f"Invalid CIF format: {cif}. Expected letter + 7 digits + check character"
            )

        org_type, digits, check_char = match.groups()

        # Calculate check digit using core module
        expected_check = cif_core.calculate_check_digit(digits, org_type)

        # Validate check character based on organization type
        if org_type in cif_core.LETTER_CHECK_TYPES:
            # Must be a letter
            if not check_char.isalpha():
                raise ValueError(
                    f"Invalid CIF check character: {cif}. "
                    f"Organization type {org_type} requires a letter"
                )
            if check_char != expected_check:
                raise ValueError(
                    f"Invalid CIF check character: {cif}. "
                    f"Expected {expected_check}, got {check_char}"
                )
        elif org_type in cif_core.NUMBER_CHECK_TYPES:
            # Must be a number
            if not check_char.isdigit():
                raise ValueError(
                    f"Invalid CIF check character: {cif}. "
                    f"Organization type {org_type} requires a digit"
                )
            if check_char != expected_check:
                raise ValueError(
                    f"Invalid CIF check character: {cif}. "
                    f"Expected {expected_check}, got {check_char}"
                )
        else:
            # Can be either letter or number, but must match
            if check_char != expected_check:
                # Try the alternative format
                if expected_check.isdigit():
                    alt_check = str((10 - int(expected_check)) % 10)
                else:
                    alt_check = expected_check
                if check_char != alt_check:
                    raise ValueError(
                        f"Invalid CIF check character: {cif}. "
                        f"Expected {expected_check} or {alt_check}, got {check_char}"
                    )


__all__ = ["CIFValidator"]
