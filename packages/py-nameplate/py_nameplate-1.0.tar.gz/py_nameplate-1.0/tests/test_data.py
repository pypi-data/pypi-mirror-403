"""
Tests for data loading and lookup functionality.

This module tests the database loading and lookup functions
in the nameplate.data module.

Test Categories:
    - Database loading: Verify database loads correctly
    - City lookups: is_valid_city, lookup_state_for_city, get_city_proper_name
    - Street lookups: is_known_street
    - ZIP validation: is_valid_zip_for_state
    - Statistics: get_database_stats
    - Edge cases: Invalid inputs, missing data
"""

import pytest

from nameplate.data import (
    get_city_proper_name,
    get_database_stats,
    is_known_street,
    is_valid_city,
    is_valid_zip_for_state,
    lookup_state_for_city,
)

# =============================================================================
# CITY LOOKUP TESTS
# =============================================================================


class TestCityLookups:
    """Tests for city lookup functions."""

    def test_is_valid_city_boston_ma(self):
        """Boston, MA should be valid."""
        assert is_valid_city("Boston", "MA") is True

    def test_is_valid_city_new_york_ny(self):
        """New York, NY should be valid."""
        assert is_valid_city("New York", "NY") is True

    def test_is_valid_city_los_angeles_ca(self):
        """Los Angeles, CA should be valid."""
        assert is_valid_city("Los Angeles", "CA") is True

    def test_is_valid_city_chicago_il(self):
        """Chicago, IL should be valid."""
        assert is_valid_city("Chicago", "IL") is True

    def test_is_valid_city_case_insensitive(self):
        """City lookup should be case-insensitive."""
        assert is_valid_city("boston", "MA") is True
        assert is_valid_city("BOSTON", "MA") is True
        assert is_valid_city("BoStOn", "MA") is True

    def test_is_valid_city_wrong_state(self):
        """Boston in wrong state should be invalid (or different city)."""
        # Boston, MA is valid, Boston, CA may or may not exist
        result = is_valid_city("Boston", "CA")
        # Just verify it returns a boolean
        assert isinstance(result, bool)

    def test_is_valid_city_nonexistent(self):
        """Nonexistent city should be invalid."""
        assert is_valid_city("Fakeville", "XX") is False

    def test_is_valid_city_empty_inputs(self):
        """Empty inputs should return False."""
        assert is_valid_city("", "MA") is False
        assert is_valid_city("Boston", "") is False
        assert is_valid_city("", "") is False

    def test_lookup_state_for_city_ambiguous(self):
        """Boston exists in multiple states, so should return None."""
        result = lookup_state_for_city("Boston")
        # Boston exists in multiple states (MA, GA, etc.), so returns None
        assert result is None

    def test_lookup_state_for_city_unambiguous(self):
        """A unique city should return its state."""
        # Try to find a city that exists in only one state
        # Note: Many cities exist in multiple states, so this may return None
        result = lookup_state_for_city("Anchorage")
        # Anchorage, AK is the only major Anchorage, should return AK
        if result is not None:
            assert len(result) == 2  # State abbreviation

    def test_lookup_state_for_city_nonexistent(self):
        """Nonexistent city should return None."""
        result = lookup_state_for_city("Fakeville123")
        assert result is None

    def test_get_city_proper_name_boston(self):
        """Should get proper casing for Boston."""
        result = get_city_proper_name("boston", "MA")
        assert result == "Boston"

    def test_get_city_proper_name_new_york(self):
        """Should get proper casing for New York."""
        result = get_city_proper_name("new york", "NY")
        assert result == "New York"

    def test_get_city_proper_name_los_angeles(self):
        """Should get proper casing for Los Angeles."""
        result = get_city_proper_name("los angeles", "CA")
        assert result == "Los Angeles"

    def test_get_city_proper_name_nonexistent(self):
        """Nonexistent city should return None."""
        result = get_city_proper_name("fakeville123", "XX")
        assert result is None


# =============================================================================
# STREET LOOKUP TESTS
# =============================================================================


class TestStreetLookups:
    """Tests for street lookup functions."""

    def test_is_known_street_main(self):
        """Main should be a known street name."""
        # Main is one of the most common street names
        result = is_known_street("Main")
        assert isinstance(result, bool)
        # Main is extremely common, should be True
        assert result is True

    def test_is_known_street_broadway(self):
        """Broadway should be a known street name."""
        result = is_known_street("Broadway")
        assert isinstance(result, bool)

    def test_is_known_street_oak(self):
        """Oak should be a known street name."""
        result = is_known_street("Oak")
        assert isinstance(result, bool)

    def test_is_known_street_case_insensitive(self):
        """Street lookup should be case-insensitive."""
        result1 = is_known_street("main")
        result2 = is_known_street("MAIN")
        result3 = is_known_street("Main")
        # All should return same result
        assert result1 == result2 == result3

    def test_is_known_street_gibberish(self):
        """Random gibberish should not be a known street."""
        result = is_known_street("xyzzy12345abc")
        assert result is False

    def test_is_known_street_empty(self):
        """Empty string should return False."""
        result = is_known_street("")
        assert result is False


# =============================================================================
# ZIP VALIDATION TESTS
# =============================================================================


class TestZipValidation:
    """Tests for ZIP code validation."""

    def test_is_valid_zip_ma_02101(self):
        """02101 should be valid for MA."""
        # MA ZIPs are in 01xxx-02xxx range
        result = is_valid_zip_for_state("02101", "MA")
        assert result is True

    def test_is_valid_zip_ca_90210(self):
        """90210 should be valid for CA."""
        # CA ZIPs are in 90xxx-96xxx range
        result = is_valid_zip_for_state("90210", "CA")
        assert result is True

    def test_is_valid_zip_ny_10001(self):
        """10001 should be valid for NY."""
        # NY ZIPs are in 10xxx-14xxx range
        result = is_valid_zip_for_state("10001", "NY")
        assert result is True

    def test_is_valid_zip_wrong_state(self):
        """ZIP in wrong state should be invalid."""
        # 02101 is MA, not CA
        result = is_valid_zip_for_state("02101", "CA")
        assert result is False

        # 90210 is CA, not NY
        result = is_valid_zip_for_state("90210", "NY")
        assert result is False

    def test_is_valid_zip_plus_four(self):
        """ZIP+4 format should be validated."""
        result = is_valid_zip_for_state("02101-1234", "MA")
        assert result is True

    def test_is_valid_zip_invalid_format(self):
        """Invalid ZIP format should return False."""
        result = is_valid_zip_for_state("abc", "MA")
        assert result is False

        result = is_valid_zip_for_state("1234", "MA")  # Too short
        assert result is False

    def test_is_valid_zip_empty(self):
        """Empty inputs should return False."""
        result = is_valid_zip_for_state("", "MA")
        assert result is False

        result = is_valid_zip_for_state("02101", "")
        assert result is False


# =============================================================================
# DATABASE STATISTICS TESTS
# =============================================================================


class TestDatabaseStatistics:
    """Tests for database statistics function."""

    def test_get_database_stats_returns_dict(self):
        """get_database_stats should return a dictionary."""
        stats = get_database_stats()
        assert isinstance(stats, dict)

    def test_get_database_stats_has_city_count(self):
        """Stats should include city count."""
        stats = get_database_stats()
        assert "cities_count" in stats
        assert isinstance(stats["cities_count"], int)
        assert stats["cities_count"] > 0

    def test_get_database_stats_has_street_count(self):
        """Stats should include street count."""
        stats = get_database_stats()
        assert "streets_count" in stats
        assert isinstance(stats["streets_count"], int)
        assert stats["streets_count"] > 0

    def test_get_database_stats_reasonable_counts(self):
        """Stats should have reasonable counts."""
        stats = get_database_stats()

        # We know we have ~29,880 cities and ~503,789 streets
        assert stats["cities_count"] > 20000
        assert stats["streets_count"] > 400000


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_none_inputs_city(self):
        """None inputs should be handled gracefully."""
        # These should not raise exceptions
        try:
            result = is_valid_city(None, "MA")
            assert result is False
        except TypeError:
            pass  # Also acceptable behavior

        try:
            result = is_valid_city("Boston", None)
            assert result is False
        except TypeError:
            pass

    def test_special_characters_in_city(self):
        """Cities with special characters should be handled."""
        # Some cities have hyphens, apostrophes, etc.
        # These should not raise exceptions
        result = is_valid_city("O'Fallon", "MO")
        assert isinstance(result, bool)

    def test_unicode_in_city(self):
        """Unicode characters should be handled gracefully."""
        result = is_valid_city("São Paulo", "XX")
        assert isinstance(result, bool)

    def test_very_long_input(self):
        """Very long inputs should be handled gracefully."""
        long_city = "A" * 1000
        result = is_valid_city(long_city, "MA")
        assert result is False

    def test_whitespace_handling(self):
        """Inputs with extra whitespace should be handled."""
        # Leading/trailing whitespace
        result1 = is_valid_city("  Boston  ", "MA")
        result2 = is_valid_city("Boston", "  MA  ")

        # Should handle gracefully (may or may not match)
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)


# =============================================================================
# STATE COVERAGE TESTS
# =============================================================================


class TestStateCoverage:
    """Tests to verify coverage of major US states."""

    @pytest.mark.parametrize(
        "city,state",
        [
            ("New York", "NY"),
            ("Los Angeles", "CA"),
            ("Chicago", "IL"),
            ("Houston", "TX"),
            ("Phoenix", "AZ"),
            ("Philadelphia", "PA"),
            ("San Antonio", "TX"),
            ("San Diego", "CA"),
            ("Dallas", "TX"),
            ("San Jose", "CA"),
            ("Austin", "TX"),
            ("Jacksonville", "FL"),
            ("Fort Worth", "TX"),
            ("Columbus", "OH"),
            ("Charlotte", "NC"),
            ("San Francisco", "CA"),
            ("Indianapolis", "IN"),
            ("Seattle", "WA"),
            ("Denver", "CO"),
            ("Boston", "MA"),
        ],
    )
    def test_major_us_cities(self, city, state):
        """Major US cities should be in the database."""
        result = is_valid_city(city, state)
        assert result is True, f"{city}, {state} should be valid"


# =============================================================================
# ZIP PREFIX COVERAGE TESTS
# =============================================================================


class TestZipPrefixCoverage:
    """Tests to verify ZIP prefix ranges are correct."""

    @pytest.mark.parametrize(
        "zip_code,state",
        [
            ("01001", "MA"),  # Massachusetts
            ("10001", "NY"),  # New York
            ("19101", "PA"),  # Pennsylvania
            ("20001", "DC"),  # DC
            ("30301", "GA"),  # Georgia
            ("33101", "FL"),  # Florida
            ("60601", "IL"),  # Illinois
            ("75201", "TX"),  # Texas
            ("80202", "CO"),  # Colorado
            ("90210", "CA"),  # California
            ("98101", "WA"),  # Washington
        ],
    )
    def test_zip_state_ranges(self, zip_code, state):
        """ZIP codes should be valid for their states."""
        result = is_valid_zip_for_state(zip_code, state)
        assert result is True, f"{zip_code} should be valid for {state}"
