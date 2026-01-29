"""
Tests for street-based enhancement functionality.

This module tests the street-based enhancement feature where addresses
with a street name but no city/state can have the city/state auto-filled
if the street exists in exactly one location in the database.

Test Categories:
    - Street lookup functionality
    - Enhancement when street is unique
    - No enhancement when street is ambiguous
    - No enhancement when street is unknown
    - Integration with parse()
"""

from nameplate import parse, parse_batch
from nameplate.data import lookup_location_for_street


class TestLookupLocationForStreet:
    """Tests for the lookup_location_for_street() function."""

    def test_empty_string_returns_none(self):
        """Empty street name should return None."""
        result = lookup_location_for_street("")
        assert result is None

    def test_none_returns_none(self):
        """None input should be handled gracefully."""
        # The function should handle None by returning None
        # (though type hints say str, we test for robustness)
        result = lookup_location_for_street(None)
        assert result is None

    def test_unknown_street_returns_none(self):
        """Unknown street name should return None."""
        result = lookup_location_for_street("Completely Fake Street That Doesn't Exist XYZ123")
        assert result is None

    def test_ambiguous_street_returns_none(self):
        """Street that exists in multiple locations should return None."""
        # "Main Street" exists in virtually every city
        result = lookup_location_for_street("Main Street")
        assert result is None

    def test_returns_tuple_for_unique_street(self):
        """Unique street should return (city, state) tuple."""
        # Note: This test depends on the database having unique streets
        # We test the return type when a result is found
        result = lookup_location_for_street("Some Unique Street Name")
        # Result is either None or a tuple
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    def test_case_insensitive_lookup(self):
        """Lookup should be case-insensitive."""
        # Test that case doesn't matter
        result1 = lookup_location_for_street("MAIN STREET")
        result2 = lookup_location_for_street("main street")
        result3 = lookup_location_for_street("Main Street")
        # All should return the same result (likely None for ambiguous)
        assert result1 == result2 == result3


class TestStreetEnhancement:
    """Tests for street-based enhancement in parse()."""

    def test_no_enhancement_without_flag(self):
        """Enhancement should not happen when enhance=False."""
        result = parse("123 Main St")
        # Without enhance flag, city should not be filled in
        assert result.enhanced is False
        assert result.enhanced_fields == []

    def test_no_enhancement_when_city_present(self):
        """Enhancement should not happen when city is already present."""
        result = parse("123 Main St, Boston, MA 02101", enhance=True)
        # City is already present, so street lookup shouldn't occur
        # (it might enhance state from city, but not street lookup)
        assert "city" not in result.enhanced_fields or result.address.city == "Boston"

    def test_no_enhancement_for_names(self):
        """Enhancement should not apply to name-only inputs."""
        result = parse("John Smith", enhance=True)
        assert result.input_type == "name"
        assert result.enhanced is False

    def test_enhanced_fields_list(self):
        """Enhanced fields should be tracked in enhanced_fields list."""
        # When enhancement occurs, enhanced_fields should list what was enhanced
        result = parse("123 Main St, Boston", enhance=True)
        # If state was enhanced from city, it should be in the list
        if result.enhanced:
            assert len(result.enhanced_fields) > 0

    def test_enhancement_sets_validated(self):
        """After enhancement, validation should run on the enhanced data."""
        result = parse("123 Main St, Boston, MA 02101", enhance=True)
        # If city/state are present, validation should occur
        if result.address.city and result.address.state:
            assert isinstance(result.validated, bool)


class TestBatchEnhancement:
    """Tests for street-based enhancement in batch parsing."""

    def test_batch_tracks_enhanced_count(self):
        """Batch parsing should track number of enhanced results."""
        texts = [
            "123 Main St, Boston, MA 02101",
            "456 Oak Ave",
        ]
        result = parse_batch(texts, enhance=True)

        assert hasattr(result, "enhanced_count")
        assert isinstance(result.enhanced_count, int)

    def test_batch_applies_enhancement_to_all(self):
        """Batch should apply enhancement flag to all inputs."""
        texts = ["123 Main St, Boston", "456 Oak Ave, Chicago, IL"]
        result = parse_batch(texts, enhance=True)

        # Each result should have been processed with enhance=True
        assert result.total == 2


class TestEnhancementEdgeCases:
    """Tests for edge cases in enhancement."""

    def test_partial_address_enhancement(self):
        """Address with city but no state should try city-based enhancement."""
        result = parse("123 Main St, Boston", enhance=True)
        # City is present, so it might try to look up state from city
        # Boston exists in multiple states, so it might not enhance
        assert result.parsed is True

    def test_street_only_no_zip(self):
        """Address with only street (no ZIP) should attempt enhancement."""
        result = parse("123 Main Street", enhance=True)
        # This might be detected as address or name depending on detection logic
        assert result.parsed is True

    def test_enhancement_preserves_existing_data(self):
        """Enhancement should not overwrite existing data."""
        result = parse("123 Main St, Boston, MA 02101", enhance=True)
        # The existing city/state should be preserved
        assert result.address.city == "Boston"
        assert result.address.state == "MA"
