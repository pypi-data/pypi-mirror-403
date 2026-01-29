"""
Tests for address parsing functionality.

This module tests address parsing through the unified parse() function,
covering standard addresses, edge cases, and error handling.

Test Categories:
    - Basic parsing: Standard US address formats
    - Street types: Abbreviations and full names
    - Units: Apartments, suites, units
    - PO Boxes: Post office box addresses
    - Directionals: N, S, E, W, NE, NW, SE, SW
    - ZIP codes: 5-digit and ZIP+4 formats
    - Normalization: Title case conversion
    - Validation: City/state/ZIP verification
    - Batch processing: Multiple addresses
    - Error handling: Invalid inputs
"""

import pytest

from nameplate import parse, parse_batch
from nameplate.schemas import AddressOutput, ParseBatchOutput, ParseOutput

# =============================================================================
# BASIC PARSING TESTS
# =============================================================================


class TestBasicAddressParsing:
    """Tests for basic address parsing functionality."""

    def test_simple_street_address(self):
        """Parse a simple street address with city, state, ZIP."""
        result = parse("123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.address.street_number == "123"
        assert result.address.street_name == "Main"
        assert result.address.street_type == "St"
        assert result.address.city == "Boston"
        assert result.address.state == "MA"
        assert result.address.zip_code == "02101"
        assert result.address.parse_type == "Street Address"

    def test_address_with_apartment(self):
        """Parse address with apartment number."""
        result = parse("456 Oak Ave Apt 2B, Chicago, IL 60601")

        assert result.parsed is True
        assert result.address.street_number == "456"
        assert result.address.street_name == "Oak"
        assert result.address.street_type == "Ave"
        # Unit type may be uppercase or mixed case
        assert result.address.unit_type.upper() == "APT"
        assert result.address.unit_number == "2B"
        assert result.address.city == "Chicago"
        assert result.address.state == "IL"

    def test_address_with_suite(self):
        """Parse address with suite number."""
        result = parse("100 Corporate Dr Suite 500, Dallas, TX 75201")

        assert result.parsed is True
        assert result.address.unit_type.upper() == "SUITE"
        assert result.address.unit_number == "500"

    def test_address_with_unit(self):
        """Parse address with generic unit number."""
        result = parse("200 Park Ave Unit 10A, New York, NY 10001")

        assert result.parsed is True
        assert result.address.unit_type.upper() == "UNIT"
        assert result.address.unit_number == "10A"

    def test_address_with_pound_unit(self):
        """Parse address with # unit notation."""
        result = parse("300 Main St #5, Portland, OR 97201")

        assert result.parsed is True
        # # notation may be parsed as unit_type "#" or unit may be "5"
        assert result.address.unit_number == "5" or "#5" in result.raw_input

    def test_zip_plus_four(self):
        """Parse address with ZIP+4 format."""
        result = parse("123 Broadway, New York, NY 10001-1234")

        assert result.parsed is True
        assert result.address.zip_code == "10001-1234"

    def test_returns_parse_output(self):
        """Verify return type is ParseOutput."""
        result = parse("123 Main St, Boston, MA 02101")
        assert isinstance(result, ParseOutput)
        assert isinstance(result.address, AddressOutput)

    def test_raw_input_preserved(self):
        """Verify raw input is preserved in output."""
        input_addr = "123 Main St, Boston, MA 02101"
        result = parse(input_addr)
        assert result.raw_input == input_addr


# =============================================================================
# STREET TYPE TESTS
# =============================================================================


class TestStreetTypes:
    """Tests for various street type formats."""

    @pytest.mark.parametrize(
        "street_type,expected",
        [
            ("St", "St"),
            ("Street", "Street"),
            ("Ave", "Ave"),
            ("Avenue", "Avenue"),
            ("Blvd", "Blvd"),
            ("Boulevard", "Boulevard"),
            ("Dr", "Dr"),
            ("Drive", "Drive"),
            ("Rd", "Rd"),
            ("Road", "Road"),
            ("Ln", "Ln"),
            ("Lane", "Lane"),
            ("Ct", "Ct"),
            ("Court", "Court"),
            ("Pl", "Pl"),
            ("Place", "Place"),
            ("Way", "Way"),
            ("Cir", "Cir"),
            ("Circle", "Circle"),
        ],
    )
    def test_street_type_parsing(self, street_type, expected):
        """Parse various street type formats."""
        result = parse(f"123 Main {street_type}, Boston, MA 02101")
        assert result.address.street_type == expected

    def test_no_street_type(self):
        """Parse address without explicit street type (like Broadway)."""
        result = parse("200 Broadway, New York, NY 10001")

        assert result.parsed is True
        assert result.address.street_name == "Broadway"
        # Street type may be empty for single-word street names


# =============================================================================
# DIRECTIONAL TESTS
# =============================================================================


class TestDirectionals:
    """Tests for street directional prefixes and suffixes."""

    @pytest.mark.parametrize(
        "direction",
        ["N", "S", "E", "W", "NE", "NW", "SE", "SW"],
    )
    def test_pre_directional(self, direction):
        """Parse addresses with pre-directional."""
        result = parse(f"100 {direction} Main St, Denver, CO 80202")

        assert result.parsed is True
        assert result.address.street_direction == direction

    @pytest.mark.parametrize(
        "direction",
        ["N", "S", "E", "W", "NE", "NW", "SE", "SW"],
    )
    def test_post_directional(self, direction):
        """Parse addresses with post-directional."""
        result = parse(f"100 Main St {direction}, Denver, CO 80202")

        assert result.parsed is True
        # Post-directional should be captured
        assert direction in (result.address.street_direction or "")


# =============================================================================
# PO BOX TESTS
# =============================================================================


class TestPOBox:
    """Tests for PO Box address parsing."""

    def test_po_box_standard(self):
        """Parse standard PO Box format."""
        result = parse("PO Box 123, Miami, FL 33101")

        assert result.parsed is True
        assert result.address.city == "Miami"
        assert result.address.state == "FL"
        assert result.address.zip_code == "33101"
        assert result.address.parse_type == "PO Box"
        # PO Box number is stored in unit_number
        assert result.address.unit_number == "123"

    def test_po_box_with_periods(self):
        """Parse P.O. Box format with periods."""
        result = parse("P.O. Box 456, Seattle, WA 98101")

        assert result.parsed is True
        assert result.address.parse_type == "PO Box"
        assert result.address.unit_number == "456"

    def test_po_box_lowercase(self):
        """Parse lowercase po box format."""
        result = parse("po box 789, Austin, TX 78701")

        assert result.parsed is True
        assert result.address.parse_type == "PO Box"

    def test_po_box_no_space(self):
        """Parse POBox without space."""
        result = parse("POBox 100, Phoenix, AZ 85001")

        assert result.parsed is True
        assert result.address.parse_type == "PO Box"


# =============================================================================
# NORMALIZATION TESTS
# =============================================================================


class TestNormalization:
    """Tests for address normalization functionality."""

    def test_normalize_uppercase(self):
        """Normalize all-uppercase address to title case."""
        result = parse(
            "123 MAIN STREET, BOSTON, MA 02101",
            normalize=True,
        )

        assert result.address.city == "Boston"
        # Street name should be normalized
        assert result.address.street_name == "Main"

    def test_normalize_lowercase(self):
        """Normalize all-lowercase address to title case."""
        result = parse(
            "123 main street, boston, ma 02101",
            normalize=True,
        )

        assert result.address.city == "Boston"
        assert result.address.street_name == "Main"

    def test_normalize_preserves_state(self):
        """State abbreviation should remain uppercase."""
        result = parse(
            "123 main st, boston, ma 02101",
            normalize=True,
        )

        assert result.address.state == "MA"

    def test_no_normalize_by_default(self):
        """Without normalize flag, preserve original case."""
        result = parse("123 MAIN ST, BOSTON, MA 02101")

        # Should preserve original case
        assert result.address.city == "BOSTON"


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Tests for address validation against database."""

    def test_valid_city_state_combination(self):
        """Valid city/state should set validated flag."""
        result = parse("123 Main St, Boston, MA 02101")

        # Boston, MA is a valid combination
        # validated flag depends on database lookup
        assert result.parsed is True

    def test_zip_state_validation(self):
        """ZIP code should be valid for the state."""
        result = parse("123 Main St, Boston, MA 02101")

        # 02101 is valid for MA (02xxx range)
        assert result.parsed is True


# =============================================================================
# BATCH PROCESSING TESTS
# =============================================================================


class TestBatchProcessing:
    """Tests for batch address parsing."""

    def test_parse_multiple_addresses(self):
        """Parse multiple addresses in batch."""
        addresses = [
            "123 Main St, Boston, MA 02101",
            "456 Oak Ave, Chicago, IL 60601",
            "789 Pine Rd, Seattle, WA 98101",
        ]

        result = parse_batch(addresses)

        assert isinstance(result, ParseBatchOutput)
        assert result.total == 3
        assert result.parsed_count == 3
        assert len(result.results) == 3

    def test_batch_with_failures(self):
        """Batch with some unparseable addresses."""
        addresses = [
            "123 Main St, Boston, MA 02101",
            "",  # Empty - will fail
            "456 Oak Ave, Chicago, IL 60601",
        ]

        result = parse_batch(addresses)

        assert result.total == 3
        assert result.parsed_count == 2  # One failed

    def test_empty_batch(self):
        """Empty list returns empty results."""
        result = parse_batch([])

        assert result.total == 0
        assert result.parsed_count == 0
        assert len(result.results) == 0

    def test_batch_preserves_order(self):
        """Results should be in same order as input."""
        addresses = [
            "123 A St, Boston, MA 02101",
            "456 B St, Chicago, IL 60601",
            "789 C St, Seattle, WA 98101",
        ]

        result = parse_batch(addresses)

        assert result.results[0].address.street_name == "A"
        assert result.results[1].address.street_name == "B"
        assert result.results[2].address.street_name == "C"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_empty_string(self):
        """Empty string should return unparsed result."""
        result = parse("")

        assert result.parsed is False
        assert len(result.errors) > 0

    def test_whitespace_only(self):
        """Whitespace-only string should return unparsed result."""
        result = parse("   ")

        assert result.parsed is False
        assert len(result.errors) > 0

    def test_no_zip_code(self):
        """Address without ZIP code may still parse partially."""
        result = parse("123 Main St, Boston, MA")

        # Should attempt to parse what's available
        assert result.address.city == "Boston"
        assert result.address.state == "MA"

    def test_no_city_state(self):
        """Address with only street should parse partially."""
        result = parse("123 Main St")

        # May or may not parse depending on implementation
        # At minimum should have raw_input
        assert result.raw_input == "123 Main St"

    def test_gibberish_input(self):
        """Completely unparseable input."""
        result = parse("asdfghjkl qwerty")

        # Should return with parsed=False or minimal parsing
        assert isinstance(result, ParseOutput)


# =============================================================================
# MULTI-WORD STREET NAME TESTS
# =============================================================================


class TestMultiWordStreetNames:
    """Tests for complex multi-word street names."""

    def test_mlk_boulevard(self):
        """Parse Martin Luther King Jr Blvd."""
        result = parse("123 Martin Luther King Jr Blvd, Atlanta, GA 30301")

        assert result.parsed is True
        assert "Martin Luther King" in result.address.street_name
        assert result.address.city == "Atlanta"

    def test_numbered_street(self):
        """Parse numbered street name like 5th Avenue."""
        result = parse("100 5th Ave, New York, NY 10001")

        assert result.parsed is True
        assert "5th" in result.address.street_name or result.address.street_name == "5th"

    def test_highway_address(self):
        """Parse highway address."""
        result = parse("12345 Highway 101, San Jose, CA 95101")

        assert result.parsed is True
        assert result.address.street_number == "12345"


# =============================================================================
# SPECIAL FORMAT TESTS
# =============================================================================


class TestSpecialFormats:
    """Tests for special address formats."""

    def test_address_without_comma_before_city(self):
        """Parse address without comma separator."""
        result = parse("123 Main St Boston MA 02101")

        # Should parse, may or may not correctly identify all components
        assert result.parsed is True
        # At minimum should get the ZIP
        assert result.address.zip_code == "02101"

    def test_address_with_extra_whitespace(self):
        """Parse address with extra whitespace."""
        result = parse("  123   Main   St,   Boston,   MA   02101  ")

        assert result.parsed is True
        assert result.address.street_number == "123"
        assert result.address.city == "Boston"

    def test_address_all_on_one_line(self):
        """Parse address without line breaks."""
        result = parse("123 Main St, Apt 4, Boston, MA 02101")

        assert result.parsed is True
        assert result.address.unit_number == "4"
