"""
Data loading utilities for nameplate.

This module provides functions for loading and querying the SQLite database
that contains US city and street name data. The database is built from
CSV source files using the scripts/build_data.py script.

Database Tables:
    cities: City/state combinations for validation
        - city: Original city name (proper casing)
        - city_upper: Uppercase for case-insensitive lookup
        - state: Two-letter state code

    streets: Known street names for validation
        - name: Original street name
        - name_upper: Uppercase for case-insensitive lookup

Key Functions:
    is_valid_city: Check if a city/state combination exists in the database
    is_known_street: Check if a street name exists in the database
    lookup_state_for_city: Find the state for a city (if unambiguous)
    is_valid_zip_for_state: Validate ZIP code prefix against state ranges

Usage:
    >>> from nameplate.data import is_valid_city, lookup_state_for_city
    >>>
    >>> is_valid_city("Boston", "MA")
    True
    >>>
    >>> is_valid_city("Boston", "CA")  # Wrong state
    False
    >>>
    >>> lookup_state_for_city("Springfield")  # Ambiguous - exists in many states
    None

Performance Notes:
    - Database connection is cached for efficiency
    - All lookups use indexed queries for O(log n) performance
    - All lookups are case-insensitive
    - Functions fail open (return False/None) if database is unavailable

Error Handling:
    All functions are designed to fail gracefully. If the database file
    is missing or corrupted, functions will return False or None rather
    than raising exceptions. This allows parsing to continue even without
    validation capability.
"""

import sqlite3
from functools import lru_cache
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Directory containing the database file
# This is relative to this module's location
DATA_DIR = Path(__file__).parent

# Database file path
DB_PATH = DATA_DIR / "nameplate.db"

# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_connection() -> sqlite3.Connection | None:
    """
    Get a connection to the SQLite database (cached).

    The connection is cached to avoid reopening the database on every query.
    Uses lru_cache with maxsize=1 since we only need one connection.

    Returns:
        Database connection, or None if database is unavailable

    Notes:
        - The database is opened in read-only mode
        - Returns None rather than raising if file is missing
        - Connection is configured for optimal read performance
    """
    if not DB_PATH.exists():
        return None

    try:
        # Open in read-only mode with URI
        conn = sqlite3.connect(
            f"file:{DB_PATH}?mode=ro",
            uri=True,
            check_same_thread=False,  # Safe for read-only access
        )

        # Optimize for read performance
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA cache_size = -2000")  # 2MB cache

        return conn

    except Exception:
        return None


def _execute_query(sql: str, params: tuple = ()) -> list | None:
    """
    Execute a read query and return results.

    Args:
        sql: SQL query string with ? placeholders
        params: Tuple of parameter values

    Returns:
        List of result rows, or None if query failed
    """
    conn = _get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.execute(sql, params)
        return cursor.fetchall()
    except Exception:
        return None


# -----------------------------------------------------------------------------
# City Validation Functions
# -----------------------------------------------------------------------------


def is_valid_city(city: str, state: str) -> bool:
    """
    Check if a city/state combination exists in the database.

    This validates that a city exists within a specific state. For example,
    "Boston" is valid for "MA" but not for "CA". Checks both the main cities
    table and the street_locations table (which includes smaller communities).

    Args:
        city: City name to validate (case-insensitive)
        state: Two-letter state abbreviation (case-insensitive)

    Returns:
        True if the city/state combination exists in either the cities
        or street_locations table, False if not found or database unavailable

    Examples:
        >>> is_valid_city("Boston", "MA")
        True
        >>> is_valid_city("boston", "ma")  # Case-insensitive
        True
        >>> is_valid_city("Boston", "CA")  # Wrong state
        False
        >>> is_valid_city("Atlanta", "GA")  # In street_locations only
        True
        >>> is_valid_city("Fakeville", "XX")
        False

    Notes:
        - Lookup is case-insensitive
        - Returns False (not an error) if database is unavailable
        - An empty city or state will return False
    """
    if not city or not state:
        return False

    city_upper = city.strip().upper()
    state_upper = state.strip().upper()

    # Check cities table first
    sql = """
        SELECT 1 FROM cities
        WHERE city_upper = ? AND state = ?
        LIMIT 1
    """
    result = _execute_query(sql, (city_upper, state_upper))
    if result is not None and len(result) > 0:
        return True

    # Also check street_locations table (has additional communities)
    sql = """
        SELECT 1 FROM street_locations
        WHERE city_upper = ? AND state = ?
        LIMIT 1
    """
    result = _execute_query(sql, (city_upper, state_upper))
    return result is not None and len(result) > 0


def lookup_state_for_city(city: str) -> str | None:
    """
    Look up the state for a given city name.

    This is used by the 'enhance' feature to fill in missing state codes.
    Only returns a state if the city name is unambiguous (exists in exactly
    one state). Cities like "Springfield" that exist in multiple states
    will return None.

    Args:
        city: City name to look up (case-insensitive)

    Returns:
        Two-letter state abbreviation if city is unambiguous,
        None if city is not found, exists in multiple states, or database unavailable

    Examples:
        >>> lookup_state_for_city("Evanston")  # Exists in IL, IN, WY
        None
        >>> lookup_state_for_city("Springfield")  # Many states
        None
        >>> lookup_state_for_city("Fakeville")
        None

    Notes:
        - Only returns a state if city exists in exactly one state
        - Returns None for safety if there's any ambiguity
    """
    if not city:
        return None

    sql = """
        SELECT DISTINCT state FROM cities
        WHERE city_upper = ?
    """

    result = _execute_query(sql, (city.strip().upper(),))

    if result is None or len(result) != 1:
        # No results, or ambiguous (multiple states)
        return None

    return result[0][0]


def get_city_proper_name(city: str, state: str) -> str | None:
    """
    Get the properly-cased city name from the database.

    This is useful for normalizing city names to their official casing.
    For example, "NEW YORK" or "new york" would return "New York".

    Args:
        city: City name to look up (case-insensitive)
        state: Two-letter state abbreviation (case-insensitive)

    Returns:
        The city name with proper casing if found, None otherwise

    Examples:
        >>> get_city_proper_name("NEW YORK", "NY")
        'New York'
        >>> get_city_proper_name("los angeles", "CA")
        'Los Angeles'
    """
    if not city or not state:
        return None

    sql = """
        SELECT city FROM cities
        WHERE city_upper = ? AND state = ?
        LIMIT 1
    """

    result = _execute_query(sql, (city.strip().upper(), state.strip().upper()))

    if result is None or len(result) == 0:
        return None

    return result[0][0]


# -----------------------------------------------------------------------------
# Street Validation Functions
# -----------------------------------------------------------------------------


def is_known_street(street_name: str) -> bool:
    """
    Check if a street name exists in the database.

    This is an informational check only. It helps identify recognized street
    names but does not affect the 'validated' flag on parsed addresses.
    Many valid streets may not be in the database.

    Args:
        street_name: Street name to check (case-insensitive)
            Should be just the name without number or type
            (e.g., "Main" not "123 Main Street")

    Returns:
        True if the street name is in the database,
        False if not found or database unavailable

    Examples:
        >>> is_known_street("Main")
        True  # (assuming database contains it)
        >>> is_known_street("Zzyzx")
        False  # (probably)

    Notes:
        - Returns False rather than raising if database is unavailable
        - Case-insensitive lookup
    """
    if not street_name:
        return False

    sql = """
        SELECT 1 FROM streets
        WHERE name_upper = ?
        LIMIT 1
    """

    result = _execute_query(sql, (street_name.strip().upper(),))

    return result is not None and len(result) > 0


def lookup_location_for_street(street_name: str) -> tuple[str, str] | None:
    """
    Look up the city and state for a given street name.

    This is used by the 'enhance' feature for street-based enhancement.
    Only returns a location if the street name exists in exactly one
    city/state combination. Streets that exist in multiple locations
    (e.g., "Main Street") will return None.

    Args:
        street_name: Street name to look up (case-insensitive).
            Can include the full street name with type
            (e.g., "Dunwoody Club Drive" or "Dunwoody Club Dr")

    Returns:
        Tuple of (city, state) if street is unambiguous,
        None if street is not found, exists in multiple locations,
        or database unavailable

    Examples:
        >>> lookup_location_for_street("Dunwoody Club Drive")
        ('Atlanta', 'GA')  # Unique street in one location
        >>> lookup_location_for_street("Main Street")
        None  # Exists in many cities
        >>> lookup_location_for_street("Nonexistent Boulevard")
        None  # Not in database

    Notes:
        - Only returns a location if street exists in exactly one city/state
        - Returns None for safety if there's any ambiguity
        - Case-insensitive lookup
    """
    if not street_name:
        return None

    sql = """
        SELECT DISTINCT city, state FROM street_locations
        WHERE street_name_upper = ?
    """

    result = _execute_query(sql, (street_name.strip().upper(),))

    if result is None or len(result) != 1:
        # No results, or ambiguous (multiple locations)
        return None

    return (result[0][0], result[0][1])


# -----------------------------------------------------------------------------
# ZIP Code Validation
# -----------------------------------------------------------------------------

# ZIP code prefix to state mapping
# Maps first 3 digits of ZIP code to valid state(s)
# Source: USPS ZIP code prefix allocation
#
# Note: Some ranges overlap or have exceptions; this is a simplified mapping
# that covers the vast majority of cases correctly.
ZIP_STATE_RANGES: dict[str, range] = {
    # Alabama
    "AL": range(350, 370),
    # Alaska (uses 995-999)
    "AK": range(995, 1000),
    # Arizona
    "AZ": range(850, 866),
    # Arkansas
    "AR": range(716, 730),
    # California (900-961)
    "CA": range(900, 962),
    # Colorado
    "CO": range(800, 817),
    # Connecticut (060-069)
    "CT": range(60, 70),
    # Delaware (197-199)
    "DE": range(197, 200),
    # District of Columbia (200-205)
    "DC": range(200, 206),
    # Florida (320-349)
    "FL": range(320, 350),
    # Georgia (300-319)
    "GA": range(300, 320),
    # Hawaii (967-968)
    "HI": range(967, 969),
    # Idaho (832-838)
    "ID": range(832, 839),
    # Illinois (600-629)
    "IL": range(600, 630),
    # Indiana (460-479)
    "IN": range(460, 480),
    # Iowa (500-528)
    "IA": range(500, 529),
    # Kansas (660-679)
    "KS": range(660, 680),
    # Kentucky (400-427)
    "KY": range(400, 428),
    # Louisiana (700-714)
    "LA": range(700, 715),
    # Maine (039-049)
    "ME": range(39, 50),
    # Maryland (206-219)
    "MD": range(206, 220),
    # Massachusetts (010-027)
    "MA": range(10, 28),
    # Michigan (480-499)
    "MI": range(480, 500),
    # Minnesota (550-567)
    "MN": range(550, 568),
    # Mississippi (386-397)
    "MS": range(386, 398),
    # Missouri (630-658)
    "MO": range(630, 659),
    # Montana (590-599)
    "MT": range(590, 600),
    # Nebraska (680-693)
    "NE": range(680, 694),
    # Nevada (889-898)
    "NV": range(889, 899),
    # New Hampshire (030-038)
    "NH": range(30, 39),
    # New Jersey (070-089)
    "NJ": range(70, 90),
    # New Mexico (870-884)
    "NM": range(870, 885),
    # New York (100-149)
    "NY": range(100, 150),
    # North Carolina (270-289)
    "NC": range(270, 290),
    # North Dakota (580-588)
    "ND": range(580, 589),
    # Ohio (430-459)
    "OH": range(430, 460),
    # Oklahoma (730-749)
    "OK": range(730, 750),
    # Oregon (970-979)
    "OR": range(970, 980),
    # Pennsylvania (150-196)
    "PA": range(150, 197),
    # Rhode Island (028-029)
    "RI": range(28, 30),
    # South Carolina (290-299)
    "SC": range(290, 300),
    # South Dakota (570-577)
    "SD": range(570, 578),
    # Tennessee (370-385)
    "TN": range(370, 386),
    # Texas (750-799)
    "TX": range(750, 800),
    # Utah (840-847)
    "UT": range(840, 848),
    # Vermont (050-059)
    "VT": range(50, 60),
    # Virginia (220-246)
    "VA": range(220, 247),
    # Washington (980-994)
    "WA": range(980, 995),
    # West Virginia (247-268)
    "WV": range(247, 269),
    # Wisconsin (530-549)
    "WI": range(530, 550),
    # Wyoming (820-831)
    "WY": range(820, 832),
}


def is_valid_zip_for_state(zip_code: str, state: str) -> bool:
    """
    Check if a ZIP code prefix is valid for the given state.

    Uses the first 3 digits of the ZIP code to validate against known
    state ranges. This is a quick sanity check, not authoritative validation.

    Args:
        zip_code: 5 or 9 digit ZIP code (e.g., "02101" or "02101-1234")
        state: Two-letter state abbreviation

    Returns:
        True if the ZIP prefix is valid for the state,
        False if invalid, or if inputs are malformed

    Examples:
        >>> is_valid_zip_for_state("02101", "MA")  # Boston
        True
        >>> is_valid_zip_for_state("90210", "CA")  # Beverly Hills
        True
        >>> is_valid_zip_for_state("02101", "CA")  # MA ZIP in CA
        False

    Notes:
        - Only checks the first 3 digits (ZIP prefix)
        - Some edge cases may not be caught (overlapping ranges)
        - Returns False for unknown states
    """
    if not zip_code or not state:
        return False

    state_upper = state.strip().upper()

    if state_upper not in ZIP_STATE_RANGES:
        return False

    try:
        # Extract first 3 digits from ZIP
        # Handle both "12345" and "12345-6789" formats
        zip_clean = zip_code.strip().replace("-", "")
        if len(zip_clean) < 3:
            return False

        prefix = int(zip_clean[:3])

        return prefix in ZIP_STATE_RANGES[state_upper]

    except (ValueError, IndexError):
        return False


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------


def get_database_stats() -> dict:
    """
    Get statistics about the loaded database.

    This is useful for debugging and verifying that the database is loaded.

    Returns:
        Dictionary with database information:
        - available: True if database is accessible
        - cities_count: Number of city records
        - streets_count: Number of street records
    """
    stats = {
        "available": False,
        "cities_count": 0,
        "streets_count": 0,
    }

    conn = _get_connection()
    if conn is None:
        return stats

    stats["available"] = True

    try:
        # Count cities
        result = conn.execute("SELECT COUNT(*) FROM cities").fetchone()
        if result:
            stats["cities_count"] = result[0]

        # Count streets
        result = conn.execute("SELECT COUNT(*) FROM streets").fetchone()
        if result:
            stats["streets_count"] = result[0]

    except Exception:
        pass

    return stats


# -----------------------------------------------------------------------------
# Module Exports
# -----------------------------------------------------------------------------

__all__ = [
    "is_valid_city",
    "lookup_state_for_city",
    "get_city_proper_name",
    "is_known_street",
    "lookup_location_for_street",
    "is_valid_zip_for_state",
    "get_database_stats",
]
