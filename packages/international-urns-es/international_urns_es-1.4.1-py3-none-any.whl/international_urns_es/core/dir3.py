"""Core constants and functions for DIR3 (Directorio Común).

DIR3 is the Common Directory of units and offices of the Spanish Public Administration.
Format: 9 character alphanumeric code.
Examples: E00010201, A01000001, L01000001, GE0000001, O00000001

This module contains the shared business logic for DIR3 validation, extraction,
and generation to maintain consistency across the codebase.
"""

import re
from re import Pattern

# Regular expression pattern for DIR3 with single-letter prefix
# Group 1: Single-letter administration level identifier (E, A, L, U, I, J, O)
# Group 2: 8-digit identifier
PATTERN_SINGLE: Pattern[str] = re.compile(r"^([EALUIJO])(\d{8})$", re.IGNORECASE)

# Regular expression pattern for DIR3 with double-letter prefix
# Group 1: Double-letter administration level identifier (GE, EC, EA, LA)
# Group 2: 7-digit identifier
PATTERN_DOUBLE: Pattern[str] = re.compile(r"^(GE|EC|EA|LA)(\d{7})$", re.IGNORECASE)

# Valid single-letter administration level codes (+ 8 digits)
SINGLE_LETTER_PREFIXES: list[str] = ["E", "A", "L", "U", "I", "J", "O"]

# Valid double-letter administration level codes (+ 7 digits)
DOUBLE_LETTER_PREFIXES: list[str] = ["GE", "EC", "EA", "LA"]

# Administration level mappings
# Maps administration level code to full name
ADMIN_LEVELS: dict[str, str] = {
    "E": "Administración del Estado",
    "A": "Administración Autonómica",
    "L": "Administración Local",
    "U": "Universidades",
    "I": "Otras Instituciones",
    "J": "Administración de Justicia",
    "O": "Oficinas",
    "GE": "Unidad de Gestión Económica-Presupuestaria",
    "EC": "Entidades Colaboradoras",
    "EA": "Administración del Estado (no RCP)",
    "LA": "Entidades del sector público local",
}

# Autonomous communities catalog (code INE)
# Used for extracting metadata from 'A' (Autonomous Administration) codes
AUTONOMOUS_COMMUNITIES: dict[str, str] = {
    "01": "Andalucía",
    "02": "Aragón",
    "03": "Principado de Asturias",
    "04": "Illes Balears",
    "05": "Canarias",
    "06": "Cantabria",
    "07": "Castilla y León",
    "08": "Castilla-La Mancha",
    "09": "Cataluña",
    "10": "Comunitat Valenciana",
    "11": "Extremadura",
    "12": "Galicia",
    "13": "Comunidad de Madrid",
    "14": "Región de Murcia",
    "15": "Comunidad Foral de Navarra",
    "16": "País Vasco",
    "17": "La Rioja",
    "18": "Ciudad de Ceuta",
    "19": "Ciudad de Melilla",
}

# Geographic entity types catalog
# Used for extracting metadata from 'L' (Local Administration) codes
GEOGRAPHIC_ENTITIES: dict[str, str] = {
    "01": "Municipio",
    "02": "Provincia",
    "03": "Isla",
    "04": "Entidad Local Menor",
    "05": "Mancomunidad",
    "06": "Comarca",
    "07": "Área Metropolitana",
    "08": "Otras Agrupaciones",
    "10": "País",
    "20": "Comunidad Autónoma",
    "00": "SIN DATO",
}

# Province codes catalog (INE codes)
# Used for extracting province metadata from 'L' (Local Administration) codes
PROVINCE_CODES: dict[str, str] = {
    "01": "Álava",
    "02": "Albacete",
    "03": "Alicante",
    "04": "Almería",
    "05": "Ávila",
    "06": "Badajoz",
    "07": "Baleares",
    "08": "Barcelona",
    "09": "Burgos",
    "10": "Cáceres",
    "11": "Cádiz",
    "12": "Castellón",
    "13": "Ciudad Real",
    "14": "Córdoba",
    "15": "A Coruña",
    "16": "Cuenca",
    "17": "Girona",
    "18": "Granada",
    "19": "Guadalajara",
    "20": "Guipúzcoa",
    "21": "Huelva",
    "22": "Huesca",
    "23": "Jaén",
    "24": "León",
    "25": "Lleida",
    "26": "La Rioja",
    "27": "Lugo",
    "28": "Madrid",
    "29": "Málaga",
    "30": "Murcia",
    "31": "Navarra",
    "32": "Ourense",
    "33": "Asturias",
    "34": "Palencia",
    "35": "Las Palmas",
    "36": "Pontevedra",
    "37": "Salamanca",
    "38": "Santa Cruz de Tenerife",
    "39": "Cantabria",
    "40": "Segovia",
    "41": "Sevilla",
    "42": "Soria",
    "43": "Tarragona",
    "44": "Teruel",
    "45": "Toledo",
    "46": "Valencia",
    "47": "Valladolid",
    "48": "Vizcaya",
    "49": "Zamora",
    "50": "Zaragoza",
    "51": "Ceuta",
    "52": "Melilla",
}


__all__ = [
    "PATTERN_SINGLE",
    "PATTERN_DOUBLE",
    "SINGLE_LETTER_PREFIXES",
    "DOUBLE_LETTER_PREFIXES",
    "ADMIN_LEVELS",
    "AUTONOMOUS_COMMUNITIES",
    "GEOGRAPHIC_ENTITIES",
    "PROVINCE_CODES",
]
