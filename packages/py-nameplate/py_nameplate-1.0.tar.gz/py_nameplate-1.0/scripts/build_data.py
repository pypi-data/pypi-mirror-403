#!/usr/bin/env python3
"""
Convert CSV data files to SQLite database for fast lookups.

This script reads the raw CSV source files (cities.csv, streets.csv) and
builds an optimized SQLite database. The resulting database provides fast
indexed lookups for validation queries.

Database File Created:
    src/nameplate/data/nameplate.db - Single SQLite database containing:
        - cities table: city/state validation
        - streets table: street name validation

Usage:
    python scripts/build_data.py

    Run this after refresh_data.py to rebuild database from fresh CSV data.

Notes:
    - SQLite is cross-platform and part of Python's standard library
    - Creates a single .db file (much cleaner than dbm's 3 files)
    - Indexes are created for fast lookups
    - Existing database file is overwritten
"""

import csv
import sqlite3
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Get the project root directory (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Directory where raw CSV source files are stored
DATA_DIR = PROJECT_ROOT / "data"

# Output database file path (inside the package)
OUTPUT_DIR = PROJECT_ROOT / "src" / "nameplate" / "data"
DB_PATH = OUTPUT_DIR / "nameplate.db"

# -----------------------------------------------------------------------------
# State Name to Code Mapping
# -----------------------------------------------------------------------------

# Maps full state names (as they appear in streets.csv) to 2-letter abbreviations
# This is needed because streets.csv uses full names like "Alabama" in area3_name
STATE_NAME_TO_CODE: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    # Territories
    "Puerto Rico": "PR",
    "Virgin Islands": "VI",
    "Guam": "GU",
    "American Samoa": "AS",
    "Northern Mariana Islands": "MP",
}

# -----------------------------------------------------------------------------
# Database Schema
# -----------------------------------------------------------------------------

# SQL statements to create tables and indexes
CREATE_TABLES_SQL = """
-- Cities table: stores city/state combinations for validation
-- Key lookup is by (city_upper, state) for case-insensitive matching
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,           -- Original city name (proper casing)
    city_upper TEXT NOT NULL,     -- Uppercase for case-insensitive lookup
    state TEXT NOT NULL           -- Two-letter state code (uppercase)
);

-- Index for fast city/state validation lookups
CREATE INDEX IF NOT EXISTS idx_cities_lookup ON cities(city_upper, state);

-- Index for state-only lookups (finding all cities in a state)
CREATE INDEX IF NOT EXISTS idx_cities_state ON cities(state);

-- Streets table: stores known street names for validation
-- This is informational only - helps identify recognized street names
CREATE TABLE IF NOT EXISTS streets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,           -- Original street name
    name_upper TEXT NOT NULL      -- Uppercase for case-insensitive lookup
);

-- Unique index on uppercase name (also enforces no duplicates)
CREATE UNIQUE INDEX IF NOT EXISTS idx_streets_name ON streets(name_upper);

-- Street locations table: maps street names to their city/state locations
-- This enables street-based enhancement: looking up city/state from street name
-- A street may exist in multiple cities, so we store all locations
CREATE TABLE IF NOT EXISTS street_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    street_name TEXT NOT NULL,           -- Original street name (e.g., "Dunwoody Club Drive")
    street_name_upper TEXT NOT NULL,     -- Uppercase for case-insensitive lookup
    city TEXT NOT NULL,                  -- City name (e.g., "Atlanta")
    city_upper TEXT NOT NULL,            -- Uppercase for case-insensitive lookup
    state TEXT NOT NULL                  -- 2-letter state code (e.g., "GA")
);

-- Index for fast street name lookups
CREATE INDEX IF NOT EXISTS idx_street_locations_name ON street_locations(street_name_upper);

-- Unique constraint to prevent duplicate street/city/state combinations
CREATE UNIQUE INDEX IF NOT EXISTS idx_street_locations_unique
    ON street_locations(street_name_upper, city_upper, state);
"""

# -----------------------------------------------------------------------------
# Database Builders
# -----------------------------------------------------------------------------


def create_database() -> sqlite3.Connection:
    """
    Create a fresh SQLite database with the required schema.

    Returns:
        Open database connection
    """
    # Remove existing database if present
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Create new database
    conn = sqlite3.connect(str(DB_PATH))

    # Enable WAL mode for better write performance during bulk insert
    conn.execute("PRAGMA journal_mode=WAL")

    # Create tables and indexes
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()

    return conn


def build_cities_table(conn: sqlite3.Connection) -> tuple[int, int]:
    """
    Populate the cities table from the cities CSV file.

    The cities table enables validation of city/state combinations
    and lookup of proper city name casing.

    CSV Format Expected:
        ID,STATE_CODE,STATE_NAME,CITY,COUNTY,LATITUDE,LONGITUDE

    Args:
        conn: Open SQLite database connection

    Returns:
        Tuple of (records_inserted, errors_encountered)
    """
    csv_path = DATA_DIR / "cities.csv"

    print("Building cities table...")
    print(f"  Source: {csv_path}")

    if not csv_path.exists():
        print(f"  ERROR: Source file not found: {csv_path}")
        print("  Run 'python scripts/refresh_data.py' first.")
        return 0, 1

    records = 0
    errors = 0

    # Prepare insert statement
    insert_sql = """
        INSERT INTO cities (city, city_upper, state)
        VALUES (?, ?, ?)
    """

    # Read CSV and insert in batches for performance
    batch = []
    batch_size = 1000

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Extract city and state from the row
                city = row["CITY"].strip()
                state = row["STATE_CODE"].strip().upper()

                if not city or not state:
                    errors += 1
                    continue

                # Add to batch
                batch.append((city, city.upper(), state))
                records += 1

                # Insert batch when full
                if len(batch) >= batch_size:
                    conn.executemany(insert_sql, batch)
                    batch = []

            except KeyError as e:
                if errors < 5:
                    print(f"  WARNING: Missing column {e} in row")
                errors += 1

            except Exception as e:
                if errors < 5:
                    print(f"  WARNING: Error processing row: {e}")
                errors += 1

    # Insert remaining records
    if batch:
        conn.executemany(insert_sql, batch)

    conn.commit()

    print(f"  Inserted: {records:,} cities")
    if errors > 0:
        print(f"  Errors: {errors}")

    return records, errors


def build_streets_table(conn: sqlite3.Connection) -> tuple[int, int]:
    """
    Populate the streets table from the streets CSV file.

    The streets table stores known street names for validation.
    This is informational only - helps identify recognized street names.

    CSV Format (StNamesLab format):
        Delimiter: $ (dollar sign)
        Columns: osm_name, st_name, area1_code, area1_name, ...
        We use 'st_name' which contains normalized street names

    Args:
        conn: Open SQLite database connection

    Returns:
        Tuple of (records_inserted, errors_encountered)
    """
    csv_path = DATA_DIR / "streets.csv"

    print("Building streets table...")
    print(f"  Source: {csv_path}")

    if not csv_path.exists():
        print(f"  SKIPPED: Source file not found: {csv_path}")
        print("  Street validation will not be available.")
        print("  Run 'python scripts/refresh_data.py' to download.")
        return 0, 0

    records = 0
    errors = 0
    seen_names = set()  # Track duplicates in memory for speed

    # Prepare insert statement
    insert_sql = """
        INSERT OR IGNORE INTO streets (name, name_upper)
        VALUES (?, ?)
    """

    # Read CSV and insert in batches
    batch = []
    batch_size = 10000  # Larger batches for streets (many more records)

    print("  Processing (this may take a minute for large files)...")

    with open(csv_path, newline="", encoding="utf-8") as f:
        # StNamesLab CSV uses $ as delimiter
        reader = csv.DictReader(f, delimiter="$")

        name_column = "st_name"

        for row in reader:
            try:
                # Extract street name and strip whitespace
                street_name = row[name_column].strip()

                if not street_name:
                    continue

                # Skip duplicates (check in memory first for speed)
                name_upper = street_name.upper()
                if name_upper in seen_names:
                    continue

                seen_names.add(name_upper)

                # Add to batch
                batch.append((street_name, name_upper))
                records += 1

                # Insert batch when full
                if len(batch) >= batch_size:
                    conn.executemany(insert_sql, batch)
                    batch = []

                    # Progress indicator
                    if records % 100000 == 0:
                        print(f"    Processed {records:,} unique names...")

            except KeyError as e:
                if errors < 5:
                    print(f"  WARNING: Missing column {e} in row")
                errors += 1

            except Exception as e:
                if errors < 5:
                    print(f"  WARNING: Error processing row: {e}")
                errors += 1

    # Insert remaining records
    if batch:
        conn.executemany(insert_sql, batch)

    conn.commit()

    print(f"  Inserted: {records:,} unique street names")
    if errors > 0:
        print(f"  Errors: {errors}")

    return records, errors


def build_street_locations_table(conn: sqlite3.Connection) -> tuple[int, int]:
    """
    Populate the street_locations table from the streets CSV file.

    The street_locations table maps street names to their city/state locations.
    This enables the "street-based enhancement" feature: when an address has
    a street name but no city/state, we can look up the location if the street
    exists in exactly one city.

    CSV Format (StNamesLab format):
        Delimiter: $ (dollar sign)
        Columns: osm_name, st_name, area1_code, area1_name, area2_code, area2_name,
                 area3_code, area3_name, lon, lat
        - st_name: Normalized street name
        - area1_name: City name
        - area3_name: State name (full name, e.g., "Alabama")

    Args:
        conn: Open SQLite database connection

    Returns:
        Tuple of (records_inserted, errors_encountered)
    """
    csv_path = DATA_DIR / "streets.csv"

    print("Building street_locations table...")
    print(f"  Source: {csv_path}")

    if not csv_path.exists():
        print(f"  SKIPPED: Source file not found: {csv_path}")
        print("  Street-based enhancement will not be available.")
        return 0, 0

    records = 0
    errors = 0
    skipped_states = set()  # Track unknown state names

    # Track unique combinations to avoid duplicates
    # Key: (street_name_upper, city_upper, state)
    seen_locations: set[tuple[str, str, str]] = set()

    # Prepare insert statement
    insert_sql = """
        INSERT OR IGNORE INTO street_locations
            (street_name, street_name_upper, city, city_upper, state)
        VALUES (?, ?, ?, ?, ?)
    """

    # Read CSV and insert in batches
    batch = []
    batch_size = 10000

    print("  Processing (this may take a minute for large files)...")

    with open(csv_path, newline="", encoding="utf-8") as f:
        # StNamesLab CSV uses $ as delimiter
        reader = csv.DictReader(f, delimiter="$")

        for row in reader:
            try:
                # Extract fields from CSV
                street_name = row["st_name"].strip()
                city = row["area1_name"].strip()
                state_name = row["area3_name"].strip()

                if not street_name or not city or not state_name:
                    continue

                # Convert state name to 2-letter code
                state = STATE_NAME_TO_CODE.get(state_name)
                if not state:
                    # Track unknown state names for debugging
                    if state_name not in skipped_states:
                        skipped_states.add(state_name)
                        if len(skipped_states) <= 5:
                            print(f"  WARNING: Unknown state name: {state_name}")
                    errors += 1
                    continue

                # Create uppercase versions for case-insensitive lookup
                street_name_upper = street_name.upper()
                city_upper = city.upper()

                # Skip duplicates (check in memory first for speed)
                location_key = (street_name_upper, city_upper, state)
                if location_key in seen_locations:
                    continue

                seen_locations.add(location_key)

                # Add to batch
                batch.append((street_name, street_name_upper, city, city_upper, state))
                records += 1

                # Insert batch when full
                if len(batch) >= batch_size:
                    conn.executemany(insert_sql, batch)
                    batch = []

                    # Progress indicator
                    if records % 100000 == 0:
                        print(f"    Processed {records:,} unique locations...")

            except KeyError as e:
                if errors < 5:
                    print(f"  WARNING: Missing column {e} in row")
                errors += 1

            except Exception as e:
                if errors < 5:
                    print(f"  WARNING: Error processing row: {e}")
                errors += 1

    # Insert remaining records
    if batch:
        conn.executemany(insert_sql, batch)

    conn.commit()

    print(f"  Inserted: {records:,} unique street/city/state combinations")
    if errors > 0:
        print(f"  Errors: {errors}")
    if skipped_states:
        print(f"  Unknown states skipped: {len(skipped_states)}")

    return records, errors


def optimize_database(conn: sqlite3.Connection) -> None:
    """
    Optimize the database after bulk inserts.

    This runs VACUUM and ANALYZE to compact the database and
    update query planner statistics.

    Args:
        conn: Open SQLite database connection
    """
    print("Optimizing database...")

    # Switch back to DELETE journal mode before VACUUM
    # (WAL mode doesn't support VACUUM into a smaller file)
    conn.execute("PRAGMA journal_mode=DELETE")

    # Analyze tables to update statistics for query planner
    conn.execute("ANALYZE")

    # Vacuum to compact the database file
    conn.execute("VACUUM")

    conn.commit()
    print("  Done")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    """
    Main entry point for the build script.

    Returns:
        Exit code: 0 for success, 1 for critical failures
    """
    print("=" * 60)
    print("Nameplate Database Builder")
    print("=" * 60)
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output: {DB_PATH}")
    print()

    # Create fresh database
    conn = create_database()

    # Track overall results
    total_records = 0
    total_errors = 0

    try:
        # Build cities table
        records, errors = build_cities_table(conn)
        total_records += records
        total_errors += errors
        print()

        # Build streets table
        records, errors = build_streets_table(conn)
        total_records += records
        total_errors += errors
        print()

        # Build street_locations table (for street-based enhancement)
        records, errors = build_street_locations_table(conn)
        total_records += records
        total_errors += errors
        print()

        # Optimize database
        optimize_database(conn)
        print()

    finally:
        conn.close()

    # Print summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total records: {total_records:,}")
    print(f"  Total errors: {total_errors}")
    print()

    # Report file size
    if DB_PATH.exists():
        size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"  Database file: {DB_PATH.name} ({size_mb:.1f} MB)")
    print()

    if total_records == 0:
        print("WARNING: No records were processed. Check source files.")
        return 1

    print("Database build complete.")
    return 0


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
