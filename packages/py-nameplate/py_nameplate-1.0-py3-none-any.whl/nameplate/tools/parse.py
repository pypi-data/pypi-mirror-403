"""
Unified parsing module - single entry point for all parsing.

This module provides a unified parse() function that uses token-based segmentation
to separate name and address components from a single input string.

Key Functions:
    parse: Parse a single input string (auto-segments name and address)
    parse_batch: Batch parse multiple input strings

Algorithm Overview:
    1. TOKENIZE: Split input into words
    2. SEGMENT: Find boundary between name and address
       - Scan for first numeric token that's NOT a name suffix (III, 1ST, etc.)
       - Verify remaining tokens have street indicators
    3. PARSE ADDRESS: Work backwards from end
       - Extract ZIP, state, city, unit, then street components
       - Enhance from database if city/state missing
    4. PARSE NAME: Use remaining tokens

Street-Based Enhancement:
    When enhance=True and an address has a street name but no city/state,
    the parser will look up the street in the database. If the street exists
    in exactly one location, the city and state are auto-filled.

Usage:
    >>> from nameplate import parse
    >>>
    >>> # Parse a contact (name + address)
    >>> result = parse("John Smith 100 Dunwoody Club Dr", enhance=True)
    >>> result.name.first
    'John'
    >>> result.name.last
    'Smith'
    >>> result.address.street_number
    '100'
    >>> result.address.city  # Auto-filled from database
    'Atlanta'
    >>>
    >>> # Parse address only
    >>> result = parse("123 Main St, Boston, MA 02101")
    >>> result.address.city
    'Boston'
"""

import re

from nameplate.schemas import (
    AddressOutput,
    NameOutput,
    ParseBatchOutput,
    ParseOutput,
)

# =============================================================================
# NAME PARSING CONSTANTS
# =============================================================================

# Common name prefixes (titles/honorifics)
# These appear before the first name
NAME_PREFIXES: set[str] = {
    # Civilian
    "MR",
    "MRS",
    "MS",
    "MISS",
    "MX",
    # Professional
    "DR",
    "PROF",
    "PROFESSOR",
    # Religious
    "REV",
    "REVEREND",
    "FR",
    "FATHER",
    "SR",
    "SISTER",
    "BR",
    "BROTHER",
    "RABBI",
    "IMAM",
    "PASTOR",
    # Legal/Political
    "HON",
    "HONORABLE",
    "JUDGE",
    "JUSTICE",
    "PRES",
    "PRESIDENT",
    "VP",
    "GOV",
    "GOVERNOR",
    "SEN",
    "SENATOR",
    "REP",
    "REPRESENTATIVE",
    "MAYOR",
    "COUNCILMAN",
    "COUNCILWOMAN",
    "AMB",
    "AMBASSADOR",
    # Military - General Officers
    "GEN",
    "GENERAL",
    "LTG",
    "LT GEN",
    "LIEUTENANT GENERAL",
    "MG",
    "MAJ GEN",
    "MAJOR GENERAL",
    "BG",
    "BRIG GEN",
    "BRIGADIER GENERAL",
    # Military - Field Officers
    "COL",
    "COLONEL",
    "LTC",
    "LT COL",
    "LIEUTENANT COLONEL",
    "MAJ",
    "MAJOR",
    # Military - Company Officers
    "CPT",
    "CAPT",
    "CAPTAIN",
    "LT",
    "1LT",
    "2LT",
    "LIEUTENANT",
    "ENS",
    "ENSIGN",
    # Military - Enlisted
    "SGT",
    "SERGEANT",
    "CPL",
    "CORPORAL",
    "PVT",
    "PRIVATE",
    "SPC",
    "SPECIALIST",
    # Navy/Coast Guard
    "ADM",
    "ADMIRAL",
    "VADM",
    "VICE ADMIRAL",
    "RADM",
    "REAR ADMIRAL",
    "CMDR",
    "COMMANDER",
    "LCDR",
    "CDR",
    "PO",
    "PETTY OFFICER",
    # Air Force
    "CMSGT",
    "SMSGT",
    "MSGT",
    "TSGT",
    "SSGT",
}

# Common name suffixes
# These appear after the last name
NAME_SUFFIXES: set[str] = {
    # Generational
    "JR",
    "JUNIOR",
    "SR",
    "SENIOR",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "1ST",
    "2ND",
    "3RD",
    "4TH",
    "5TH",
    # Academic
    "PHD",
    "PH D",
    "MD",
    "M D",
    "DO",
    "D O",
    "JD",
    "J D",
    "DDS",
    "D D S",
    "DMD",
    "D M D",
    "DVM",
    "D V M",
    "EDD",
    "ED D",
    "DBA",
    "D B A",
    "MBA",
    "M B A",
    "MA",
    "M A",
    "MS",
    "M S",
    "MSN",
    "M S N",
    "RN",
    "R N",
    "LPN",
    "L P N",
    "CPA",
    "C P A",
    "ESQ",
    "ESQUIRE",
    "PE",
    "P E",
    # Certifications
    "CFA",
    "CFP",
    "CPCU",
    # Religious
    "DD",
    "D D",
    "THD",
    "TH D",
    # Other
    "RET",
    "RETIRED",
    "USA",
    "USAF",
    "USN",
    "USMC",
    "USCG",
}

# Last name particles (should stay with last name)
# These connect to the following word to form compound last names
# Examples: "van der Berg", "de la Cruz", "al-Rashid"
NAME_PARTICLES: set[str] = {
    # Dutch/Flemish
    "VAN",
    "VANDER",
    "VAN DER",
    "VAN DE",
    "VAN DEN",
    # German
    "VON",
    "VOM",
    "VON DER",
    # Spanish
    "DE",
    "DEL",
    "DE LA",
    "DE LAS",
    "DE LOS",
    # Portuguese
    "DA",
    "DAS",
    "DO",
    "DOS",
    # Italian
    "DI",
    "DELLA",
    "DELLE",
    "DELLO",
    "DEGLI",
    "DEI",
    "DAL",
    "DALLA",
    # French
    "LE",
    "LA",
    "DU",
    "DES",
    "DE LA",
    # Arabic
    "AL",
    "EL",
    "ABU",
    "BIN",
    "IBN",
    "AL-",
    "EL-",
    # Scottish/Irish
    "MAC",
    "MC",
    "O'",
    # Other
    "SAN",
    "SANTA",
    "SAINT",
    "ST",
    "TER",
    "TE",
    "TEN",
    "VEL",
    "VON UND ZU",
    "Y",  # Spanish conjunction (Velasquez y Garcia)
}

# Single-word particles that indicate start of last name
SINGLE_PARTICLES: set[str] = {
    "VAN",
    "VON",
    "DE",
    "DA",
    "DI",
    "LE",
    "LA",
    "DU",
    "AL",
    "EL",
    "MAC",
    "MC",
    "TER",
    "TE",
    "TEN",
    "BIN",
    "IBN",
    "ABU",
    "Y",
}

# =============================================================================
# NAME PARSING REGEX PATTERNS
# =============================================================================

# Match nickname in quotes or parentheses
# Examples: 'Robert "Bob" Smith', "Robert (Bob) Smith"
NICKNAME_PATTERN = re.compile(r'["\']([^"\']+)["\']|\(([^)]+)\)')

# Match "Last, First Middle" format
# Examples: "Smith, John", "DOE, JANE A.", "Garcia-Lopez, Maria Elena"
LAST_FIRST_PATTERN = re.compile(r"^([^,]+),\s*(.+)$")

# Match comma-separated suffixes at end
# Examples: "John Smith, Jr.", "Jane Doe, MD, PhD"
COMMA_SUFFIX_PATTERN = re.compile(r",\s*([^,]+)$")

# =============================================================================
# ADDRESS PARSING CONSTANTS
# =============================================================================

# Name suffixes that look numeric but should NOT be treated as street numbers
# These are generational suffixes that follow a person's name
NAME_SUFFIXES_NUMERIC: set[str] = {
    # Roman numerals
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    # Ordinals
    "1ST",
    "2ND",
    "3RD",
    "4TH",
    "5TH",
    "6TH",
    "7TH",
    "8TH",
    "9TH",
    "10TH",
}

# Common street type suffixes - indicates address content
STREET_TYPES: set[str] = {
    "ST",
    "STREET",
    "AVE",
    "AVENUE",
    "BLVD",
    "BOULEVARD",
    "DR",
    "DRIVE",
    "LN",
    "LANE",
    "RD",
    "ROAD",
    "CT",
    "COURT",
    "PL",
    "PLACE",
    "WAY",
    "CIR",
    "CIRCLE",
    "TRL",
    "TRAIL",
    "PKWY",
    "PARKWAY",
    "HWY",
    "HIGHWAY",
    "TER",
    "TERRACE",
    "ALY",
    "ALLEY",
    "SQ",
    "SQUARE",
    "LOOP",
    "PATH",
    "PIKE",
    "RUN",
    "WALK",
    "XING",
    "CROSSING",
}

# US state abbreviations (includes DC)
STATES: set[str] = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}

# Directional prefixes/suffixes for streets
DIRECTIONS: set[str] = {
    "N",
    "S",
    "E",
    "W",
    "NE",
    "NW",
    "SE",
    "SW",
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
}

# Unit designators
UNIT_TYPES: set[str] = {
    "APT",
    "APARTMENT",
    "SUITE",
    "STE",
    "UNIT",
    "BLDG",
    "BUILDING",
    "FL",
    "FLOOR",
    "RM",
    "ROOM",
    "#",
}

# Street type abbreviation to full name mapping (for database lookup)
STREET_TYPE_EXPANSIONS: dict[str, str] = {
    "ST": "STREET",
    "AVE": "AVENUE",
    "BLVD": "BOULEVARD",
    "DR": "DRIVE",
    "LN": "LANE",
    "RD": "ROAD",
    "CT": "COURT",
    "PL": "PLACE",
    "CIR": "CIRCLE",
    "TRL": "TRAIL",
    "PKWY": "PARKWAY",
    "HWY": "HIGHWAY",
    "TER": "TERRACE",
    "ALY": "ALLEY",
    "SQ": "SQUARE",
    "XING": "CROSSING",
}

# =============================================================================
# REGEX PATTERNS
# =============================================================================

# ZIP code pattern: 5 digits, optionally with hyphen and 4 more digits
ZIP_PATTERN = re.compile(r"^\d{5}(?:-\d{4})?$")

# Street number pattern: digits, optionally with letter suffix or hyphen
# Examples: 123, 456B, 789-A, 1234A
STREET_NUMBER_PATTERN = re.compile(r"^\d+[A-Za-z]?$|^\d+-[A-Za-z]$")

# PO Box pattern - matches "PO", "P.O.", or "POBox" at start of token
PO_BOX_PATTERN = re.compile(r"^P\.?O\.?(?:BOX)?$", re.IGNORECASE)


# =============================================================================
# TOKENIZATION
# =============================================================================


def _tokenize(text: str) -> list[str]:
    """
    Split input text into tokens (words).

    Preserves punctuation attached to tokens but normalizes whitespace.

    Args:
        text: Input string to tokenize

    Returns:
        List of tokens (words)

    Examples:
        >>> _tokenize("John Smith 100 Dunwoody Club Dr")
        ['John', 'Smith', '100', 'Dunwoody', 'Club', 'Dr']
        >>> _tokenize("Dr. John Smith Jr. 123 Main St, Boston, MA 02101")
        ['Dr.', 'John', 'Smith', 'Jr.', '123', 'Main', 'St,', 'Boston,', 'MA', '02101']
    """
    if not text:
        return []

    # Normalize whitespace and split
    return text.split()


# =============================================================================
# SEGMENTATION
# =============================================================================


def _is_street_number(token: str) -> bool:
    """
    Check if a token looks like a street number.

    Street numbers are numeric, optionally with a letter suffix.

    Args:
        token: Token to check

    Returns:
        True if token looks like a street number

    Examples:
        >>> _is_street_number("123")
        True
        >>> _is_street_number("456B")
        True
        >>> _is_street_number("Dan")
        False
    """
    # Clean trailing punctuation
    clean = token.rstrip(".,;:")
    return bool(STREET_NUMBER_PATTERN.match(clean))


def _is_name_suffix(token: str) -> bool:
    """
    Check if a token is a name suffix that looks numeric.

    These are generational suffixes (III, IV, 1ST, 2ND) that should
    not be treated as street numbers.

    Args:
        token: Token to check

    Returns:
        True if token is a numeric-looking name suffix

    Examples:
        >>> _is_name_suffix("III")
        True
        >>> _is_name_suffix("1ST")
        True
        >>> _is_name_suffix("123")
        False
    """
    clean = token.upper().rstrip(".,;:")
    return clean in NAME_SUFFIXES_NUMERIC


def _clean_token(token: str) -> str:
    """
    Remove trailing punctuation from a token.

    Args:
        token: Token to clean

    Returns:
        Token with trailing punctuation removed
    """
    return token.rstrip(".,;:")


def _has_street_indicators(tokens: list[str]) -> bool:
    """
    Check if tokens contain indicators of an address.

    Street indicators include:
    - Street type (St, Ave, Blvd, etc.)
    - State abbreviation
    - ZIP code pattern
    - PO Box pattern

    Args:
        tokens: List of tokens to check

    Returns:
        True if tokens contain address indicators

    Examples:
        >>> _has_street_indicators(["Evergreen", "Terrace"])
        True
        >>> _has_street_indicators(["Boston", "MA", "02101"])
        True
        >>> _has_street_indicators(["John", "Smith"])
        False
    """
    for token in tokens:
        clean = _clean_token(token).upper()

        # Check for street type
        if clean in STREET_TYPES:
            return True

        # Check for state abbreviation
        if clean in STATES:
            return True

        # Check for ZIP code
        if ZIP_PATTERN.match(clean):
            return True

        # Check for PO Box
        if PO_BOX_PATTERN.match(clean):
            return True

    return False


def _segment(tokens: list[str]) -> tuple[list[str], list[str]]:
    """
    Segment tokens into name and address portions.

    Finds the boundary by locating the first street number token
    that is NOT a name suffix, then verifying remaining tokens
    contain street indicators.

    Args:
        tokens: List of tokens to segment

    Returns:
        Tuple of (name_tokens, address_tokens)

    Examples:
        >>> _segment(["John", "Smith", "742", "Evergreen", "Terrace"])
        (['John', 'Smith'], ['742', 'Evergreen', 'Terrace'])
        >>> _segment(["John", "Smith", "III", "123", "Main", "St"])
        (['John', 'Smith', 'III'], ['123', 'Main', 'St'])
        >>> _segment(["John", "Smith"])
        (['John', 'Smith'], [])
    """
    # Check for PO Box pattern at start (address only, no name)
    if len(tokens) >= 1:
        # Handle "POBox" as single token
        if tokens[0].upper().startswith("POBOX"):
            return [], tokens
        # Handle "PO Box" as two tokens
        if len(tokens) >= 2 and PO_BOX_PATTERN.match(tokens[0]) and tokens[1].upper() == "BOX":
            return [], tokens

    # Also check for PO Box anywhere in the string
    for i, token in enumerate(tokens):
        # Handle "POBox" as single token
        if token.upper().startswith("POBOX"):
            return tokens[:i], tokens[i:]
        if PO_BOX_PATTERN.match(token):
            # Check if next token is "BOX"
            if i + 1 < len(tokens) and tokens[i + 1].upper() == "BOX":
                return tokens[:i], tokens[i:]

    # Scan for first street number that's not a name suffix
    for i, token in enumerate(tokens):
        if _is_street_number(token) and not _is_name_suffix(token):
            # Found potential street number
            remaining = tokens[i:]

            # Verify remaining tokens have street indicators
            if _has_street_indicators(remaining):
                return tokens[:i], tokens[i:]

    # No address found - entire input is name
    return tokens, []


# =============================================================================
# ADDRESS PARSING (BACKWARDS)
# =============================================================================


def _extract_zip(tokens: list[str]) -> tuple[str, list[str]]:
    """
    Extract ZIP code from end of tokens.

    Args:
        tokens: List of address tokens

    Returns:
        Tuple of (zip_code, remaining_tokens)
    """
    if not tokens:
        return "", tokens

    last = _clean_token(tokens[-1])
    if ZIP_PATTERN.match(last):
        return last, tokens[:-1]

    return "", tokens


def _extract_state(tokens: list[str]) -> tuple[str, list[str]]:
    """
    Extract state abbreviation from end of tokens.

    Args:
        tokens: List of address tokens

    Returns:
        Tuple of (state, remaining_tokens)
    """
    if not tokens:
        return "", tokens

    last = _clean_token(tokens[-1]).upper()
    if last in STATES:
        return last, tokens[:-1]

    return "", tokens


def _extract_city(tokens: list[str], state: str) -> tuple[str, list[str]]:
    """
    Extract city name from end of tokens.

    Handles multi-word city names by checking progressively longer
    sequences against the database.

    Args:
        tokens: List of address tokens
        state: State abbreviation (for validation)

    Returns:
        Tuple of (city, remaining_tokens)
    """
    if not tokens:
        return "", tokens

    from nameplate.data import is_valid_city

    # Try progressively longer sequences from the end (up to 4 words)
    max_words = min(4, len(tokens))

    for num_words in range(max_words, 0, -1):
        # Build city name from last N tokens
        city_tokens = tokens[-num_words:]
        city_name = " ".join(_clean_token(t) for t in city_tokens)

        # Validate against database if we have a state
        if state:
            if is_valid_city(city_name, state):
                return city_name, tokens[:-num_words]
        else:
            # Without state, accept if it looks reasonable
            # (no street types or numbers)
            has_street_type = any(_clean_token(t).upper() in STREET_TYPES for t in city_tokens)
            has_number = any(_is_street_number(t) for t in city_tokens)
            if not has_street_type and not has_number and num_words == 1:
                # Single word without indicators - might be city
                return city_name, tokens[:-num_words]

    return "", tokens


def _extract_unit(tokens: list[str]) -> tuple[str, str, list[str]]:
    """
    Extract unit designator and number from tokens.

    Looks for patterns like "Apt 2B", "Suite 100", "#5".

    Args:
        tokens: List of address tokens

    Returns:
        Tuple of (unit_type, unit_number, remaining_tokens)
    """
    if len(tokens) < 2:
        return "", "", tokens

    remaining = list(tokens)

    # Scan for unit type in the middle or end of tokens
    for i in range(len(remaining) - 1):
        clean = _clean_token(remaining[i]).upper()
        if clean in UNIT_TYPES or clean == "#":
            unit_type = clean if clean != "#" else "#"
            unit_number = _clean_token(remaining[i + 1])
            # Remove the unit type and number
            return unit_type, unit_number, remaining[:i] + remaining[i + 2 :]

    # Check for "#" attached to a number (e.g., "#5")
    for i, token in enumerate(remaining):
        if token.startswith("#") and len(token) > 1:
            return "#", token[1:], remaining[:i] + remaining[i + 1 :]

    return "", "", tokens


def _extract_street(tokens: list[str]) -> tuple[str, str, str, str]:
    """
    Extract street components from tokens.

    Order of extraction:
    1. Street number (first token if numeric)
    2. Direction (N, S, E, W) - can be prefix or suffix
    3. Street type (St, Ave, etc.) - usually last
    4. Street name - remaining tokens

    Args:
        tokens: List of address tokens

    Returns:
        Tuple of (street_number, street_name, street_type, direction)
    """
    if not tokens:
        return "", "", "", ""

    remaining = list(tokens)
    street_number = ""
    street_type = ""
    direction = ""

    # Extract street number from start
    if remaining and _is_street_number(remaining[0]):
        street_number = _clean_token(remaining[0])
        remaining = remaining[1:]

    # Extract direction prefix
    if remaining and _clean_token(remaining[0]).upper() in DIRECTIONS:
        direction = _clean_token(remaining[0]).upper()
        remaining = remaining[1:]

    # Extract street type from end
    if remaining and _clean_token(remaining[-1]).upper() in STREET_TYPES:
        street_type = _clean_token(remaining[-1])
        remaining = remaining[:-1]

    # Extract direction suffix (if not already found)
    if not direction and remaining and _clean_token(remaining[-1]).upper() in DIRECTIONS:
        direction = _clean_token(remaining[-1]).upper()
        remaining = remaining[:-1]

    # Remaining tokens are street name
    street_name = " ".join(_clean_token(t) for t in remaining)

    return street_number, street_name, street_type, direction


def _parse_po_box(tokens: list[str]) -> AddressOutput:
    """
    Parse a PO Box address.

    Args:
        tokens: List of address tokens starting with "PO Box" or "POBox"

    Returns:
        AddressOutput with PO Box components
    """
    result = AddressOutput(
        raw_input=" ".join(tokens),
        parse_type="PO Box",
    )

    remaining = list(tokens)

    # Handle "POBox" as single token (e.g., "POBox 100")
    if remaining and remaining[0].upper().startswith("POBOX"):
        # Extract box number if attached (e.g., "POBox100") or move to next token
        first_token = remaining[0]
        if len(first_token) > 5:  # "POBox" + number
            result.unit_number = first_token[5:]
            remaining = remaining[1:]
        else:
            remaining = remaining[1:]
            if remaining:
                result.unit_number = _clean_token(remaining[0])
                remaining = remaining[1:]
    else:
        # Handle "PO Box" or "P.O. Box" as separate tokens
        if remaining and PO_BOX_PATTERN.match(remaining[0]):
            remaining = remaining[1:]
        if remaining and remaining[0].upper() == "BOX":
            remaining = remaining[1:]

        # Next token should be box number
        if remaining:
            result.unit_number = _clean_token(remaining[0])
            remaining = remaining[1:]

    # Extract ZIP, state, city from remaining
    zip_code, remaining = _extract_zip(remaining)
    state, remaining = _extract_state(remaining)
    city, remaining = _extract_city(remaining, state)

    result.zip_code = zip_code
    result.state = state
    result.city = city
    result.parsed = True

    return result


def _parse_address_tokens(
    tokens: list[str],
    normalize: bool = False,
    enhance: bool = False,
) -> AddressOutput:
    """
    Parse address tokens into structured components.

    Works backwards from the end: ZIP -> State -> City -> Unit -> Street.

    Args:
        tokens: List of address tokens
        normalize: If True, normalize to title case
        enhance: If True, attempt to fill in missing data

    Returns:
        AddressOutput with parsed components
    """
    if not tokens:
        return AddressOutput()

    # Check for PO Box - handle "POBox" as single token or "PO Box" as two tokens
    if tokens[0].upper().startswith("POBOX"):
        return _parse_po_box(tokens)
    if len(tokens) >= 2:
        if PO_BOX_PATTERN.match(tokens[0]) and tokens[1].upper() == "BOX":
            return _parse_po_box(tokens)

    result = AddressOutput(
        raw_input=" ".join(tokens),
        parse_type="Street Address",
    )

    remaining = list(tokens)

    # Work backwards: ZIP -> State -> City -> Unit -> Street
    result.zip_code, remaining = _extract_zip(remaining)
    result.state, remaining = _extract_state(remaining)
    result.city, remaining = _extract_city(remaining, result.state)
    result.unit_type, result.unit_number, remaining = _extract_unit(remaining)

    street_number, street_name, street_type, direction = _extract_street(remaining)
    result.street_number = street_number
    result.street_name = street_name
    result.street_type = street_type
    result.street_direction = direction

    # Validation
    if result.city and result.state:
        from nameplate.data import is_valid_city

        result.validated = is_valid_city(result.city, result.state)

    # Mark as parsed if we got any meaningful components
    result.parsed = any(
        [
            result.street_number,
            result.street_name,
            result.unit_number,
            result.city,
            result.state,
            result.zip_code,
        ]
    )

    # Normalization
    if normalize:
        if result.street_name:
            result.street_name = result.street_name.title()
        if result.city:
            result.city = result.city.title()
        if result.street_type:
            result.street_type = result.street_type.title()

    return result


# =============================================================================
# STREET-BASED ENHANCEMENT
# =============================================================================


def _apply_street_enhancement(
    result: ParseOutput,
    address: AddressOutput,
) -> None:
    """
    Apply street-based enhancement to an address.

    If the address has a street name but no city, looks up the street in
    the database. If the street exists in exactly one location, fills in
    the city and state.

    This function modifies the address and result objects in place.

    Args:
        result: The ParseOutput to update with enhancement info
        address: The AddressOutput to potentially enhance

    Notes:
        - Only enhances if city is missing but street_name is present
        - Only fills in if street exists in exactly one location
        - Updates enhanced, enhanced_fields on result
    """
    # Skip if city already present or no street name
    if address.city or not address.street_name:
        return

    # Try to look up location from street name
    from nameplate.data import lookup_location_for_street

    # Build the full street name with type for lookup
    # Expand abbreviations to full form for database match
    street_to_lookup = address.street_name
    if address.street_type:
        street_type_upper = address.street_type.upper()
        # Expand abbreviation if present
        street_type_full = STREET_TYPE_EXPANSIONS.get(street_type_upper, street_type_upper)
        street_to_lookup = f"{address.street_name} {street_type_full}"

    location = lookup_location_for_street(street_to_lookup)

    if location:
        city, state = location
        address.city = city
        address.state = state
        address.enhanced = True
        result.enhanced = True
        result.enhanced_fields.extend(["city", "state"])

        # Validate the enhanced address
        from nameplate.data import is_valid_city

        address.validated = is_valid_city(city, state)
        result.validated = address.validated


# =============================================================================
# NAME PARSING HELPERS
# =============================================================================


def _smart_capitalize(word: str) -> str:
    """
    Capitalize a word, handling special cases.

    Handles:
        - Mc prefix: McDonald, McArthur, McGee
        - Mac prefix: MacArthur, MacDonald
        - O' prefix: O'Brien, O'Connor, O'Malley
        - Hyphenated names: Garcia-Lopez, Jean-Pierre
        - All caps input: SMITH -> Smith

    Args:
        word: Word to capitalize

    Returns:
        Properly capitalized word

    Examples:
        >>> _smart_capitalize("MCDONALD")
        'McDonald'
        >>> _smart_capitalize("o'brien")
        "O'Brien"
        >>> _smart_capitalize("GARCIA-LOPEZ")
        'Garcia-Lopez'
    """
    if not word:
        return word

    word_lower = word.lower()

    # Handle Mc prefix: McDonald, McArthur
    if word_lower.startswith("mc") and len(word) > 2:
        return "Mc" + word[2:].capitalize()

    # Handle Mac prefix: MacArthur, MacDonald
    # But not words like "mace" or "machine"
    if word_lower.startswith("mac") and len(word) > 3:
        next_char = word[3:4].lower()
        # Common Mac names have uppercase after "Mac"
        if next_char in "acdghklmnprstwy":
            return "Mac" + word[3:].capitalize()

    # Handle O' prefix: O'Brien, O'Connor
    if word_lower.startswith("o'") and len(word) > 2:
        return "O'" + word[2:].capitalize()

    # Handle hyphenated names: Garcia-Lopez
    if "-" in word:
        parts = word.split("-")
        return "-".join(_smart_capitalize(p) for p in parts)

    # Standard capitalization
    return word.capitalize()


def _is_name_suffix_for_parsing(word: str) -> bool:
    """
    Check if a word is likely a name suffix.

    Args:
        word: Word to check

    Returns:
        True if word appears to be a suffix

    Examples:
        >>> _is_name_suffix_for_parsing("Jr.")
        True
        >>> _is_name_suffix_for_parsing("III")
        True
        >>> _is_name_suffix_for_parsing("John")
        False
    """
    clean = word.upper().rstrip(".,")
    return clean in NAME_SUFFIXES


def _is_name_prefix_for_parsing(word: str) -> bool:
    """
    Check if a word is likely a name prefix/title.

    Args:
        word: Word to check

    Returns:
        True if word appears to be a prefix

    Examples:
        >>> _is_name_prefix_for_parsing("Dr.")
        True
        >>> _is_name_prefix_for_parsing("Lt.")
        True
        >>> _is_name_prefix_for_parsing("John")
        False
    """
    clean = word.upper().rstrip(".")
    return clean in NAME_PREFIXES


def _parse_name_impl(name: str, normalize: bool = False) -> NameOutput:
    """
    Parse a full name string into structured components.

    Takes an unstructured name string and extracts components like
    prefix (title), first name, middle name, last name, suffix,
    and nickname.

    Args:
        name: The full name string to parse. Examples:
            - "John Smith"
            - "Dr. Jane Doe"
            - "Robert Johnson Jr."
            - "Smith, John"
            - 'Robert "Bob" Smith'
        normalize: If True, normalize output to title case. Handles
            special cases like McDonald, O'Brien, etc. Default False
            preserves original casing.

    Returns:
        NameOutput: A Pydantic model containing:
            - prefix: Title (e.g., "Dr.", "Mr.")
            - first: First name (e.g., "John")
            - middle: Middle name(s) (e.g., "Paul", "Jane Elizabeth")
            - last: Last name (e.g., "Smith", "van der Berg")
            - suffix: Suffix (e.g., "Jr.", "PhD")
            - nickname: Nickname if present (e.g., "Bob")
            - raw_input: Original input string
            - parsed: True if any components were extracted
            - errors: List of any parsing errors

    Examples:
        >>> result = _parse_name_impl("Dr. Martin Luther King Jr.")
        >>> result.prefix
        'Dr.'
        >>> result.first
        'Martin'
        >>> result.middle
        'Luther'
        >>> result.last
        'King'
        >>> result.suffix
        'Jr.'

        >>> result = _parse_name_impl("Smith, John")
        >>> result.first
        'John'
        >>> result.last
        'Smith'

        >>> result = _parse_name_impl('Robert "Bob" Smith')
        >>> result.nickname
        'Bob'

    Notes:
        - Empty or whitespace-only input returns an error
        - Single names (mononyms) are assigned to first name
        - Compound last names with particles are handled (van, de, etc.)
    """
    # Initialize result with raw input
    result = NameOutput(raw_input=name)

    # Handle empty input
    if not name or not name.strip():
        result.errors = ["Empty name provided"]
        return result

    # Normalize whitespace
    name = " ".join(name.split())

    # -------------------------------------------------------------------------
    # Extract nickname (quoted or parenthesized)
    # -------------------------------------------------------------------------
    nick_match = NICKNAME_PATTERN.search(name)
    if nick_match:
        # Group 1 is quoted, group 2 is parenthesized
        result.nickname = nick_match.group(1) or nick_match.group(2)
        # Remove nickname from name string
        name = name[: nick_match.start()] + name[nick_match.end() :]
        name = " ".join(name.split())  # Re-normalize whitespace

    # -------------------------------------------------------------------------
    # Handle "Last, First Middle" format
    # -------------------------------------------------------------------------
    last_first_match = LAST_FIRST_PATTERN.match(name)
    if last_first_match:
        last_part = last_first_match.group(1).strip()
        rest = last_first_match.group(2).strip()

        # Check if there are comma-separated suffixes in the "rest" part
        # e.g., "DOE, JOHN A, JR" -> last="DOE", rest="JOHN A, JR"
        suffix_parts = []
        while True:
            comma_match = COMMA_SUFFIX_PATTERN.search(rest)
            if comma_match and _is_name_suffix_for_parsing(comma_match.group(1)):
                suffix_parts.insert(0, comma_match.group(1).strip().rstrip("."))
                rest = rest[: comma_match.start()]
            else:
                break

        if suffix_parts:
            result.suffix = " ".join(suffix_parts)

        # Rebuild as "First Middle Last" for further processing
        name = rest + " " + last_part

    # -------------------------------------------------------------------------
    # Extract comma-separated suffixes from end (if not already extracted)
    # e.g., "John Smith, Jr." or "Jane Doe, MD, PhD"
    # -------------------------------------------------------------------------
    if not result.suffix:
        suffix_parts = []
        while True:
            comma_match = COMMA_SUFFIX_PATTERN.search(name)
            if comma_match and _is_name_suffix_for_parsing(comma_match.group(1)):
                suffix_parts.insert(0, comma_match.group(1).strip().rstrip("."))
                name = name[: comma_match.start()]
            else:
                break

        if suffix_parts:
            result.suffix = " ".join(suffix_parts)

    # -------------------------------------------------------------------------
    # Split into words for further processing
    # -------------------------------------------------------------------------
    words = name.split()

    if not words:
        result.errors = ["No name components found"]
        return result

    # -------------------------------------------------------------------------
    # Extract prefixes from start
    # -------------------------------------------------------------------------
    prefixes = []
    while words and _is_name_prefix_for_parsing(words[0]):
        prefixes.append(words.pop(0))

    if prefixes:
        result.prefix = " ".join(prefixes)

    # -------------------------------------------------------------------------
    # Extract suffixes from end (non-comma-separated)
    # e.g., "John Smith Jr" or "Jane Doe III"
    # -------------------------------------------------------------------------
    if not result.suffix:
        suffixes = []
        while words and _is_name_suffix_for_parsing(words[-1]):
            suffixes.insert(0, words.pop().rstrip(".,"))

        if suffixes:
            result.suffix = " ".join(suffixes)

    # -------------------------------------------------------------------------
    # Handle remaining words: first, middle(s), last
    # -------------------------------------------------------------------------
    if not words:
        # Only prefix/suffix found
        if result.prefix or result.suffix:
            result.errors = ["Only prefix/suffix found, no name"]
        else:
            result.errors = ["No name components found"]
        return result

    if len(words) == 1:
        # Single name (mononym) - assign to first
        result.first = words[0]

    elif len(words) == 2:
        # Two words: first and last
        result.first = words[0]
        result.last = words[1]

    else:
        # Three or more words: first, middle(s), last
        result.first = words[0]

        # Find where last name starts by checking for particles
        # Particles like "van", "de", "al" indicate start of last name
        last_start = len(words) - 1  # Default: last word is last name

        for i in range(1, len(words) - 1):
            word_upper = words[i].upper().rstrip("'")

            # Check if this word is a particle
            if word_upper in SINGLE_PARTICLES:
                last_start = i
                break

            # Check for two-word particles (e.g., "van der", "de la")
            if i < len(words) - 2:
                two_word = f"{words[i].upper()} {words[i + 1].upper()}"
                if two_word in NAME_PARTICLES:
                    last_start = i
                    break

        # Assign middle and last names
        result.middle = " ".join(words[1:last_start])
        result.last = " ".join(words[last_start:])

    # -------------------------------------------------------------------------
    # Determine if parsing succeeded
    # -------------------------------------------------------------------------
    result.parsed = any(
        [
            result.first,
            result.last,
            result.middle,
        ]
    )

    # -------------------------------------------------------------------------
    # Normalization: apply smart title case if requested
    # -------------------------------------------------------------------------
    if normalize:
        if result.prefix:
            # Capitalize each word in prefix
            result.prefix = " ".join(
                w.capitalize() if not w.endswith(".") else w.capitalize()
                for w in result.prefix.split()
            )
        if result.first:
            result.first = _smart_capitalize(result.first)
        if result.middle:
            result.middle = " ".join(_smart_capitalize(w) for w in result.middle.split())
        if result.last:
            result.last = _smart_capitalize(result.last)
        if result.suffix:
            # Suffixes are typically uppercase (PhD, MD) or mixed (Jr.)
            result.suffix = " ".join(
                w.upper() if len(w) <= 3 else w.capitalize() for w in result.suffix.split()
            )
        if result.nickname:
            result.nickname = _smart_capitalize(result.nickname)

    return result


# =============================================================================
# MAIN PARSING FUNCTION
# =============================================================================


def parse(
    text: str,
    normalize: bool = False,
    enhance: bool = False,
) -> ParseOutput:
    """
    Parse an input string, segmenting into name and address components.

    This is the unified entry point for all parsing. It uses token-based
    segmentation to find the boundary between name and address, then
    parses each portion independently.

    Args:
        text: The input string to parse. Can be:
            - A name: "Dr. John Smith Jr."
            - An address: "123 Main St, Boston, MA 02101"
            - A contact (name + address): "John Smith 123 Main St, Boston, MA 02101"
        normalize: If True, normalize output to title case. Default False.
        enhance: If True, attempt to fill in missing data from database.
            Enhancement includes:
            - Looking up state from city (if city present but state missing)
            - Looking up city/state from street name (if street present but
              city missing, and street exists in exactly one location)
            Default False.

    Returns:
        ParseOutput containing:
            - name: Parsed name components (NameOutput)
            - address: Parsed address components (AddressOutput)
            - raw_input: Original input string
            - input_type: Detected type ("name", "address", or "contact")
            - parsed: True if parsing succeeded
            - validated: True if address city/state validated against database
            - enhanced: True if any data was enhanced from database
            - enhanced_fields: List of fields that were enhanced
            - errors: List of any parsing errors

    Examples:
        >>> result = parse("John Smith 100 Dunwoody Club Dr", enhance=True)
        >>> result.name.first
        'John'
        >>> result.name.last
        'Smith'
        >>> result.address.street_number
        '100'
        >>> result.address.city  # Auto-filled from database
        'Atlanta'
        >>> result.enhanced
        True
        >>> result.enhanced_fields
        ['city', 'state']

        >>> result = parse("123 Main St, Boston, MA 02101")
        >>> result.input_type
        'address'
        >>> result.address.city
        'Boston'
        >>> result.validated
        True

        >>> result = parse("Dr. John Smith Jr.")
        >>> result.input_type
        'name'
        >>> result.name.prefix
        'Dr.'
        >>> result.name.first
        'John'

    Notes:
        - Empty or whitespace-only input returns with errors
        - Enhancement only fills in data when unambiguous
        - Street-based enhancement only works when street exists in one location
    """
    # Initialize result
    result = ParseOutput(raw_input=text)

    # Handle empty input
    if not text or not text.strip():
        result.errors = ["Empty input provided"]
        return result

    # Tokenize
    tokens = _tokenize(text)

    if not tokens:
        result.errors = ["No tokens found in input"]
        return result

    # Segment into name and address portions
    name_tokens, address_tokens = _segment(tokens)

    # Determine input type
    if name_tokens and address_tokens:
        result.input_type = "contact"
    elif address_tokens:
        result.input_type = "address"
    else:
        result.input_type = "name"

    # Parse name portion
    if name_tokens:
        name_str = " ".join(name_tokens)
        result.name = _parse_name_impl(name_str, normalize=normalize)
        if result.name.errors:
            result.errors.extend(result.name.errors)

    # Parse address portion
    if address_tokens:
        result.address = _parse_address_tokens(
            address_tokens,
            normalize=normalize,
            enhance=enhance,
        )
        if result.address.errors:
            result.errors.extend(result.address.errors)

        result.validated = result.address.validated

        # Apply street-based enhancement if enabled and city is missing
        if enhance and not result.address.city and result.address.street_name:
            _apply_street_enhancement(result, result.address)

    # Determine overall success
    name_parsed = result.name.parsed if name_tokens else True
    address_parsed = result.address.parsed if address_tokens else True
    result.parsed = name_parsed and address_parsed

    return result


# =============================================================================
# BATCH PARSING FUNCTION
# =============================================================================


def parse_batch(
    texts: list[str],
    normalize: bool = False,
    enhance: bool = False,
) -> ParseBatchOutput:
    """
    Parse multiple input strings in a single call.

    Each input is parsed independently using parse(), with automatic
    segmentation for each.

    Args:
        texts: List of input strings to parse. Each can be a name,
            address, or contact string.
        normalize: If True, normalize all outputs to title case. Default False.
        enhance: If True, attempt to fill in missing data. Default False.

    Returns:
        ParseBatchOutput containing:
            - results: List of ParseOutput for each input
            - total: Total number of strings processed
            - parsed_count: Number successfully parsed
            - validated_count: Number with validated addresses
            - enhanced_count: Number where data was enhanced

    Examples:
        >>> texts = [
        ...     "Dr. John Smith",
        ...     "123 Main St, Boston, MA 02101",
        ...     "Jane Doe 456 Oak Ave, Chicago, IL 60601"
        ... ]
        >>> result = parse_batch(texts)
        >>> result.total
        3
        >>> result.results[0].input_type
        'name'
        >>> result.results[1].input_type
        'address'
        >>> result.results[2].input_type
        'contact'
    """
    results = [parse(t, normalize=normalize, enhance=enhance) for t in texts]

    return ParseBatchOutput(
        results=results,
        total=len(results),
        parsed_count=sum(1 for r in results if r.parsed),
        validated_count=sum(1 for r in results if r.validated),
        enhanced_count=sum(1 for r in results if r.enhanced),
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "parse",
    "parse_batch",
]
