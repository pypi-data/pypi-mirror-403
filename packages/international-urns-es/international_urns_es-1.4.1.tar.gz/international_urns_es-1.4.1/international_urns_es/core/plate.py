"""Core constants and functions for Spanish vehicle license plates.

Spanish license plates have evolved through different formats:
- Current format (since 2000): 4 digits + 3 letters (e.g., 1234ABC)
- Old format (1971-2000): 1-2 province letters + 4 digits + 1-2 letters (e.g., M1234AB)
- Special formats: Diplomatic, official, etc.

This module contains the shared business logic for plate validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

# Regular expression pattern for current format (since 2000)
# Group 1: 4 digits
# Group 2: 3 consonants (no vowels A, E, I, O, U, and no Ñ, Q)
PATTERN_CURRENT: Pattern[str] = re.compile(r"^(\d{4})([BCDFGHJKLMNPRSTVWXYZ]{3})$", re.IGNORECASE)

# Regular expression pattern for old format (1971-2000)
# Group 1: 1-2 province letters
# Group 2: 4 digits
# Group 3: 1-2 letters
PATTERN_OLD: Pattern[str] = re.compile(r"^([A-Z]{1,2})(\d{4})([A-Z]{1,2})$", re.IGNORECASE)

# Regular expression pattern for special formats
# Group 1: Special prefix (CD, CC, E, ET, CMD, DGP, MF, MMA, PMM, CNP)
# Group 2: 4-5 digits
PATTERN_SPECIAL: Pattern[str] = re.compile(
    r"^(CD|CC|E|ET|CMD|DGP|MF|MMA|PMM|CNP)(\d{4,5})$", re.IGNORECASE
)

# Valid consonants for current format (no vowels, Ñ, or Q)
CONSONANTS: list[str] = [
    "B",
    "C",
    "D",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "R",
    "S",
    "T",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]

# Valid province codes for old format (54 codes total)
# Can be used as a set for validation or as a list for generation
PROVINCE_CODES_LIST: list[str] = [
    "A",
    "AB",
    "AL",
    "AV",
    "B",
    "BA",
    "BI",
    "BU",
    "C",
    "CA",
    "CC",
    "CE",
    "CO",
    "CR",
    "CS",
    "CU",
    "GC",
    "GI",
    "GR",
    "GU",
    "H",
    "HU",
    "J",
    "L",
    "LE",
    "LO",
    "LU",
    "M",
    "MA",
    "ML",
    "MU",
    "NA",
    "O",
    "OR",
    "P",
    "PM",
    "PO",
    "S",
    "SA",
    "SE",
    "SG",
    "SO",
    "SS",
    "T",
    "TE",
    "TF",
    "TO",
    "V",
    "VA",
    "VI",
    "Z",
    "ZA",
]

# Province codes as a set for validation (faster lookup)
PROVINCE_CODES_SET: set[str] = set(PROVINCE_CODES_LIST)

# Province code mappings (code -> full province name)
PROVINCE_NAMES: dict[str, str] = {
    "A": "Alicante",
    "AB": "Albacete",
    "AL": "Almería",
    "AV": "Ávila",
    "B": "Barcelona",
    "BA": "Badajoz",
    "BI": "Vizcaya",
    "BU": "Burgos",
    "C": "A Coruña",
    "CA": "Cádiz",
    "CC": "Cáceres",
    "CE": "Ceuta",
    "CO": "Córdoba",
    "CR": "Ciudad Real",
    "CS": "Castellón",
    "CU": "Cuenca",
    "GC": "Las Palmas",
    "GI": "Girona",
    "GR": "Granada",
    "GU": "Guadalajara",
    "H": "Huelva",
    "HU": "Huesca",
    "J": "Jaén",
    "L": "Lleida",
    "LE": "León",
    "LO": "La Rioja",
    "LU": "Lugo",
    "M": "Madrid",
    "MA": "Málaga",
    "ML": "Melilla",
    "MU": "Murcia",
    "NA": "Navarra",
    "O": "Asturias",
    "OR": "Ourense",
    "P": "Palencia",
    "PM": "Baleares",
    "PO": "Pontevedra",
    "S": "Cantabria",
    "SA": "Salamanca",
    "SE": "Sevilla",
    "SG": "Segovia",
    "SO": "Soria",
    "SS": "Guipúzcoa",
    "T": "Tarragona",
    "TE": "Teruel",
    "TF": "Santa Cruz de Tenerife",
    "TO": "Toledo",
    "V": "Valencia",
    "VA": "Valladolid",
    "VI": "Álava",
    "Z": "Zaragoza",
    "ZA": "Zamora",
}

# Special format prefixes
SPECIAL_PREFIXES: list[str] = ["CD", "CC", "E", "ET", "CMD", "DGP", "MF", "MMA", "PMM", "CNP"]

# Special plate type descriptions
SPECIAL_TYPES: dict[str, str] = {
    "CD": "Cuerpo Diplomático (Diplomatic Corps)",
    "CC": "Cuerpo Consular (Consular Corps)",
    "E": "Extranjero (Foreign)",
    "ET": "Extranjero Temporal (Temporary Foreign)",
    "CMD": "Casa de Su Majestad el Rey (Royal Household)",
    "DGP": "Dirección General de Policía (Police Directorate)",
    "MF": "Ministerio de Defensa - Fuerzas Armadas (Ministry of Defense - Armed Forces)",
    "MMA": "Ministerio de Medio Ambiente (Ministry of Environment)",
    "PMM": "Parque Móvil del Estado (State Vehicle Pool)",
    "CNP": "Cuerpo Nacional de Policía (National Police Corps)",
}

# All letters A-Z for old format ending
ALL_LETTERS: list[str] = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]


__all__ = [
    "PATTERN_CURRENT",
    "PATTERN_OLD",
    "PATTERN_SPECIAL",
    "CONSONANTS",
    "PROVINCE_CODES_LIST",
    "PROVINCE_CODES_SET",
    "PROVINCE_NAMES",
    "SPECIAL_PREFIXES",
    "SPECIAL_TYPES",
    "ALL_LETTERS",
]
