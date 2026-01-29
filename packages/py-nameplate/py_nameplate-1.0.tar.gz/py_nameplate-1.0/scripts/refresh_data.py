#!/usr/bin/env python3
"""
Fetch latest data from upstream sources and prepare for build.

This script downloads fresh copies of source data files that are used
to build the hash databases for city and street validation.

Data Sources:
    - US Cities: kelvins/US-Cities-Database (MIT License)
      Contains ~30,000 US cities with state, county, coordinates
      Format: Direct CSV download

    - Street Names: StNamesLab/StreetNamesDatabase (ODbL License)
      Contains US street names derived from OpenStreetMap
      Format: Multi-part RAR archives that must be downloaded and extracted

Usage:
    python scripts/refresh_data.py

    This will:
    1. Download cities.csv to the data/ directory
    2. Download all 7 parts of the US street names RAR archive
    3. Extract the RAR files to get the street names CSV
    4. Clean up the temporary RAR files

    After running, execute build_data.py to rebuild the hash databases.

Requirements:
    - Internet connection
    - unrar utility installed (apt-get install unrar-free)
    - rarfile Python package (uv add rarfile)

Notes:
    - Overwrites existing data files if present
    - RAR extraction requires the unrar command-line tool
    - Street data is ~7 parts x ~50MB each = ~350MB download
"""

import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Get the project root directory (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Directory where raw CSV source files are stored
DATA_DIR = PROJECT_ROOT / "data"

# Cities data source - direct CSV download
CITIES_SOURCE = {
    "url": "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv",
    "filename": "cities.csv",
    "description": "US Cities Database (~30,000 cities with state/county)",
}

# Street names data source - multi-part RAR archive
# The data is split across 7 RAR parts that must all be downloaded
STREETS_SOURCE = {
    "base_url": "https://github.com/StNamesLab/StreetNamesDatabase/raw/main/North%20America/data/",
    "parts": [
        "stn_US.part01.rar",
        "stn_US.part02.rar",
        "stn_US.part03.rar",
        "stn_US.part04.rar",
        "stn_US.part05.rar",
        "stn_US.part06.rar",
        "stn_US.part07.rar",
    ],
    "description": "US Street Names from OpenStreetMap (7-part RAR archive)",
}

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def download_file(url: str, dest: Path, description: str = "") -> bool:
    """
    Download a file from a URL to a destination path.

    Args:
        url: The URL to download from
        dest: The local file path to save to
        description: Human-readable description for progress messages

    Returns:
        True if download succeeded, False otherwise
    """
    desc = description or dest.name
    print(f"  Downloading {desc}...")

    try:
        # Download with progress indication
        urllib.request.urlretrieve(url, dest)

        # Report file size
        size_bytes = dest.stat().st_size
        if size_bytes > 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"
        print(f"    Downloaded: {size_str}")
        return True

    except urllib.error.HTTPError as e:
        print(f"    ERROR: HTTP {e.code} - {e.reason}")
        return False

    except urllib.error.URLError as e:
        print(f"    ERROR: Could not connect - {e.reason}")
        return False

    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def download_cities() -> bool:
    """
    Download the US cities CSV file.

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{CITIES_SOURCE['description']}")
    print(f"  Source: {CITIES_SOURCE['url']}")

    dest = DATA_DIR / CITIES_SOURCE["filename"]
    return download_file(CITIES_SOURCE["url"], dest, CITIES_SOURCE["filename"])


def download_and_extract_streets() -> bool:
    """
    Download all parts of the street names RAR archive and extract.

    The street names data is stored as a multi-part RAR archive on GitHub.
    We need to:
    1. Download all 7 parts to a temp directory
    2. Extract using unrar (extracts from part01, others are referenced)
    3. Move the resulting CSV to our data directory
    4. Clean up temp files

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{STREETS_SOURCE['description']}")

    # Check if unrar is available
    try:
        result = subprocess.run(
            ["unrar", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("  ERROR: unrar command not found or not working")
            print("  Install with: sudo apt-get install unrar-free")
            return False
    except FileNotFoundError:
        print("  ERROR: unrar command not found")
        print("  Install with: sudo apt-get install unrar-free")
        return False

    # Create a temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"  Temp directory: {temp_path}")

        # Download all RAR parts
        print(f"  Downloading {len(STREETS_SOURCE['parts'])} RAR parts...")
        for part in STREETS_SOURCE["parts"]:
            url = STREETS_SOURCE["base_url"] + part
            dest = temp_path / part

            if not download_file(url, dest, part):
                print(f"  ERROR: Failed to download {part}")
                return False

        # Extract using unrar
        # unrar will automatically find and use all parts when extracting part01
        print("\n  Extracting RAR archive...")
        first_part = temp_path / STREETS_SOURCE["parts"][0]

        try:
            result = subprocess.run(
                ["unrar", "x", "-o+", str(first_part), str(temp_path) + "/"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for extraction
            )

            if result.returncode != 0:
                print(f"  ERROR: unrar extraction failed")
                print(f"  stderr: {result.stderr}")
                return False

            print("    Extraction complete")

        except subprocess.TimeoutExpired:
            print("  ERROR: Extraction timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"  ERROR: Extraction failed - {e}")
            return False

        # Find the extracted CSV file
        # The file might be named stn_US.csv or similar
        print("  Looking for extracted CSV file...")
        csv_files = list(temp_path.glob("*.csv")) + list(temp_path.glob("**/*.csv"))

        if not csv_files:
            # Also check for .txt files that might be CSV format
            csv_files = list(temp_path.glob("*.txt")) + list(temp_path.glob("**/*.txt"))

        if not csv_files:
            print("  ERROR: No CSV file found in extracted archive")
            print(f"  Contents of temp dir: {list(temp_path.iterdir())}")
            # Check subdirectories too
            for item in temp_path.iterdir():
                if item.is_dir():
                    print(f"    {item.name}/: {list(item.iterdir())}")
            return False

        # Use the first (or largest) CSV file found
        if len(csv_files) > 1:
            # Pick the largest file, most likely the main data file
            csv_files.sort(key=lambda f: f.stat().st_size, reverse=True)
            print(f"  Found {len(csv_files)} CSV files, using largest: {csv_files[0].name}")

        source_csv = csv_files[0]
        dest_csv = DATA_DIR / "streets.csv"

        # Report size
        size_mb = source_csv.stat().st_size / (1024 * 1024)
        print(f"  Source file: {source_csv.name} ({size_mb:.1f} MB)")

        # Copy to data directory (can't move across filesystems)
        print(f"  Copying to {dest_csv}...")
        import shutil
        shutil.copy2(source_csv, dest_csv)
        print(f"    Done: {dest_csv}")

        return True


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    """
    Main entry point for the refresh script.

    Returns:
        Exit code: 0 for success, 1 for any failures
    """
    print("=" * 60)
    print("Nameplate Data Refresh")
    print("=" * 60)

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nData directory: {DATA_DIR}")

    # Track success/failure
    success = True

    # Download cities data
    if not download_cities():
        success = False

    # Download and extract streets data
    if not download_and_extract_streets():
        success = False

    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    cities_path = DATA_DIR / "cities.csv"
    streets_path = DATA_DIR / "streets.csv"

    if cities_path.exists():
        size_kb = cities_path.stat().st_size / 1024
        print(f"  cities.csv: {size_kb:.1f} KB")
    else:
        print("  cities.csv: MISSING")

    if streets_path.exists():
        size_mb = streets_path.stat().st_size / (1024 * 1024)
        print(f"  streets.csv: {size_mb:.1f} MB")
    else:
        print("  streets.csv: MISSING")

    print()

    if not success:
        print("Some downloads failed. Check the errors above.")
        return 1

    print("Data refresh complete.")
    print("Run 'python scripts/build_data.py' to rebuild hash databases.")
    return 0


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
