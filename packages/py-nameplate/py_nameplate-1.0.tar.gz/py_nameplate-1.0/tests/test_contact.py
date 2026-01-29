"""
Tests for contact parsing functionality.

This module tests contact parsing through the unified parse() function,
which parses combined name + address strings.

Test Categories:
    - Basic parsing: Simple name followed by address
    - Boundary detection: Finding where name ends and address begins
    - Name suffixes: Handling Jr., III, etc. before address
    - PO Box contacts: Name followed by PO Box address
    - Edge cases: Unusual formats and special characters
    - Batch processing: Multiple contacts
    - Error handling: Invalid inputs
"""

from nameplate import parse, parse_batch
from nameplate.schemas import ParseBatchOutput, ParseOutput

# =============================================================================
# BASIC PARSING TESTS
# =============================================================================


class TestBasicContactParsing:
    """Tests for basic contact parsing functionality."""

    def test_simple_contact(self):
        """Parse simple name followed by address."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.address.street_number == "123"
        assert result.address.city == "Boston"
        assert result.address.state == "MA"

    def test_contact_with_prefix(self):
        """Parse contact with name prefix."""
        result = parse("Dr. Jane Doe 456 Oak Ave, Chicago, IL 60601")

        assert result.parsed is True
        assert "Dr" in result.name.prefix
        assert result.name.first == "Jane"
        assert result.name.last == "Doe"
        assert result.address.city == "Chicago"

    def test_contact_with_suffix(self):
        """Parse contact with name suffix."""
        result = parse("John Smith Jr. 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert "Jr" in result.name.suffix
        assert result.address.street_number == "123"

    def test_returns_parse_output(self):
        """Verify return type is ParseOutput."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")
        assert isinstance(result, ParseOutput)

    def test_raw_input_preserved(self):
        """Verify raw input is preserved in output."""
        input_text = "John Smith 123 Main St, Boston, MA 02101"
        result = parse(input_text)
        assert result.raw_input == input_text


# =============================================================================
# BOUNDARY DETECTION TESTS
# =============================================================================


class TestBoundaryDetection:
    """Tests for name/address boundary detection."""

    def test_boundary_with_middle_name(self):
        """Boundary detection with middle name present."""
        result = parse("John Michael Smith 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.address.street_number == "123"

    def test_boundary_with_name_particle(self):
        """Boundary detection with name particle (van, de)."""
        result = parse("Juan de la Vega 100 N Main St, Denver, CO 80202")

        assert result.parsed is True
        assert result.name.first == "Juan"
        assert "de la" in result.name.last.lower()
        assert result.address.street_number == "100"

    def test_boundary_with_po_box(self):
        """Boundary detection with PO Box address."""
        result = parse("Mary Watson PO Box 789, Miami, FL 33101")

        assert result.parsed is True
        assert result.name.first == "Mary"
        assert result.name.last == "Watson"
        assert result.address.parse_type == "PO Box"
        # PO Box number is stored in unit_number
        assert result.address.unit_number == "789"


# =============================================================================
# ROMAN NUMERAL SUFFIX TESTS
# =============================================================================


class TestRomanNumeralSuffixes:
    """Tests for handling Roman numeral suffixes that could be confused with street numbers."""

    def test_suffix_iii_not_street_number(self):
        """Roman numeral III should be suffix, not street number."""
        result = parse("Henry Ford III 100 Auto Dr, Detroit, MI 48201")

        assert result.parsed is True
        assert result.name.first == "Henry"
        assert result.name.last == "Ford"
        assert result.name.suffix == "III"
        assert result.address.street_number == "100"

    def test_suffix_iv_not_street_number(self):
        """Roman numeral IV should be suffix, not street number."""
        result = parse("John Smith IV 200 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.suffix == "IV"
        assert result.address.street_number == "200"

    def test_suffix_ii_not_street_number(self):
        """Roman numeral II should be suffix, not street number."""
        result = parse("James Brown II 50 Oak Ave, Chicago, IL 60601")

        assert result.parsed is True
        assert result.name.suffix == "II"
        assert result.address.street_number == "50"


# =============================================================================
# COMPLEX NAME TESTS
# =============================================================================


class TestComplexNames:
    """Tests for contacts with complex names."""

    def test_full_formal_name(self):
        """Parse contact with full formal name."""
        result = parse("Dr. Martin Luther King Jr. 450 Auburn Ave, Atlanta, GA 30312")

        assert result.parsed is True
        assert "Dr" in result.name.prefix
        assert result.name.first == "Martin"
        assert result.name.middle == "Luther"
        assert result.name.last == "King"
        assert "Jr" in result.name.suffix

    def test_hyphenated_last_name(self):
        """Parse contact with hyphenated last name."""
        result = parse("Mary Watson-Parker 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.first == "Mary"
        # Hyphenated name should be preserved
        assert result.address.street_number == "123"


# =============================================================================
# ADDRESS TYPE TESTS
# =============================================================================


class TestAddressTypes:
    """Tests for different address types in contacts."""

    def test_street_address(self):
        """Parse contact with standard street address."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.address.parse_type == "Street Address"

    def test_po_box_address(self):
        """Parse contact with PO Box address."""
        result = parse("John Smith PO Box 123, Miami, FL 33101")

        assert result.parsed is True
        assert result.address.parse_type == "PO Box"
        # PO Box number is stored in unit_number
        assert result.address.unit_number == "123"

    def test_address_with_apartment(self):
        """Parse contact with apartment in address."""
        result = parse("Jane Doe 456 Oak Ave Apt 2B, Chicago, IL 60601")

        assert result.parsed is True
        # Unit type may be uppercase
        assert result.address.unit_type.upper() == "APT"
        assert result.address.unit_number == "2B"


# =============================================================================
# NORMALIZATION TESTS
# =============================================================================


class TestNormalization:
    """Tests for contact normalization functionality."""

    def test_normalize_contact(self):
        """Normalize uppercase contact to title case."""
        result = parse(
            "JOHN SMITH 123 MAIN ST, BOSTON, MA 02101",
            normalize=True,
        )

        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.address.city == "Boston"

    def test_normalize_lowercase_contact(self):
        """Normalize lowercase contact to title case."""
        result = parse(
            "john smith 123 main st, boston, ma 02101",
            normalize=True,
        )

        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_no_normalize_by_default(self):
        """Without normalize flag, preserve original case."""
        result = parse("JOHN SMITH 123 MAIN ST, BOSTON, MA 02101")

        assert result.name.first == "JOHN"
        assert result.address.city == "BOSTON"


# =============================================================================
# BATCH PROCESSING TESTS
# =============================================================================


class TestBatchProcessing:
    """Tests for batch contact parsing."""

    def test_parse_multiple_contacts(self):
        """Parse multiple contacts in batch."""
        contacts = [
            "John Smith 123 Main St, Boston, MA 02101",
            "Jane Doe 456 Oak Ave, Chicago, IL 60601",
            "Bob Johnson 789 Pine Rd, Seattle, WA 98101",
        ]

        result = parse_batch(contacts)

        assert isinstance(result, ParseBatchOutput)
        assert result.total == 3
        assert result.parsed_count == 3
        assert len(result.results) == 3

    def test_batch_with_failures(self):
        """Batch with some unparseable contacts."""
        contacts = [
            "John Smith 123 Main St, Boston, MA 02101",
            "",  # Empty - will fail
            "Jane Doe 456 Oak Ave, Chicago, IL 60601",
        ]

        result = parse_batch(contacts)

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
        contacts = [
            "Alice Smith 100 A St, Boston, MA 02101",
            "Bob Jones 200 B St, Chicago, IL 60601",
            "Carol Brown 300 C St, Seattle, WA 98101",
        ]

        result = parse_batch(contacts)

        assert result.results[0].name.first == "Alice"
        assert result.results[1].name.first == "Bob"
        assert result.results[2].name.first == "Carol"


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

    def test_name_only(self):
        """String with only name (no address) should handle gracefully."""
        result = parse("John Smith")

        # Should parse name but no address
        assert result.name.parsed is True
        assert result.input_type == "name"

    def test_address_only(self):
        """String with only address (no name) should handle gracefully."""
        result = parse("123 Main St, Boston, MA 02101")

        # Should parse address but no name
        assert result.address.parsed is True
        assert result.input_type == "address"

    def test_extra_whitespace(self):
        """Contact with extra whitespace should parse correctly."""
        result = parse("  John   Smith   123  Main  St,  Boston,  MA  02101  ")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"


# =============================================================================
# SPECIAL CASES TESTS
# =============================================================================


class TestSpecialCases:
    """Tests for special and edge cases."""

    def test_zip_plus_four(self):
        """Parse contact with ZIP+4 format."""
        result = parse("John Smith 123 Main St, Boston, MA 02101-1234")

        assert result.parsed is True
        assert result.address.zip_code == "02101-1234"

    def test_directional_in_address(self):
        """Parse contact with directional in address."""
        result = parse("John Smith 100 N Main St, Denver, CO 80202")

        assert result.parsed is True
        assert result.address.street_direction == "N"

    def test_long_street_name(self):
        """Parse contact with long street name."""
        result = parse("John Smith 123 Martin Luther King Jr Blvd, Atlanta, GA 30301")

        assert result.parsed is True
        assert "Martin Luther King" in result.address.street_name

    def test_contact_with_nickname(self):
        """Parse contact where name has nickname."""
        result = parse('Robert "Bob" Smith 123 Main St, Boston, MA 02101')

        assert result.parsed is True
        assert result.name.first == "Robert"
        assert result.name.nickname == "Bob"


# =============================================================================
# FLAG TESTS
# =============================================================================


class TestFlags:
    """Tests for output flags and indicators."""

    def test_parsed_flag_success(self):
        """Parsed flag should be True for successful parse."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")

        assert result.parsed is True
        assert result.name.parsed is True
        assert result.address.parsed is True

    def test_parsed_flag_failure(self):
        """Parsed flag should be False for failed parse."""
        result = parse("")

        assert result.parsed is False

    def test_errors_list(self):
        """Errors list should contain parsing errors."""
        result = parse("")

        assert isinstance(result.errors, list)
        assert len(result.errors) > 0


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Tests for contact validation."""

    def test_validated_flag_set(self):
        """Validated flag should reflect address validation."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")

        # Validated flag depends on database lookup
        assert isinstance(result.validated, bool)

    def test_enhanced_flag_set(self):
        """Enhanced flag should reflect enhancement status."""
        result = parse(
            "John Smith 123 Main St, Boston, MA 02101",
            enhance=True,
        )

        assert isinstance(result.enhanced, bool)
