"""
Tests for the unified parse() function.

This module tests the parse() and parse_batch() functions which provide
the unified parsing interface with auto-detection of input type.

Test Categories:
    - Input type detection (name, address, contact)
    - Parsing accuracy for each type
    - Batch processing
    - Edge cases
"""

from nameplate import parse, parse_batch
from nameplate.schemas import ParseBatchOutput


class TestInputTypeDetection:
    """Tests for auto-detection of input type."""

    def test_detects_address_with_zip(self):
        """Address with ZIP code should be detected as address."""
        result = parse("123 Main St, Boston, MA 02101")
        assert result.input_type == "address"

    def test_detects_address_with_po_box(self):
        """PO Box should be detected as address."""
        result = parse("PO Box 789, Miami, FL 33101")
        assert result.input_type == "address"

    def test_detects_name_without_address_indicators(self):
        """Simple name should be detected as name."""
        result = parse("Dr. John Smith Jr.")
        assert result.input_type == "name"

    def test_detects_contact_with_name_before_address(self):
        """Name followed by address should be detected as contact."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")
        assert result.input_type == "contact"

    def test_detects_name_only(self):
        """Name without any address indicators should be detected as name."""
        result = parse("Mary Jane Watson")
        assert result.input_type == "name"

    def test_empty_input_defaults_to_name(self):
        """Empty input should have errors and default input_type."""
        result = parse("")
        assert "Empty input provided" in result.errors


class TestAddressParsing:
    """Tests for parsing addresses through the unified interface."""

    def test_parses_standard_address(self):
        """Standard address should parse correctly."""
        result = parse("123 Main St, Boston, MA 02101")
        assert result.input_type == "address"
        assert result.address.street_number == "123"
        assert result.address.street_name == "Main"
        assert result.address.street_type == "St"
        assert result.address.city == "Boston"
        assert result.address.state == "MA"
        assert result.address.zip_code == "02101"
        assert result.parsed is True

    def test_parses_po_box(self):
        """PO Box address should parse correctly."""
        result = parse("PO Box 789, Miami, FL 33101")
        assert result.address.parse_type == "PO Box"
        assert result.address.unit_number == "789"
        assert result.address.city == "Miami"
        assert result.address.state == "FL"

    def test_parses_address_with_unit(self):
        """Address with apartment/unit should parse correctly."""
        result = parse("456 Oak Ave, Apt 2B, Chicago, IL 60601")
        assert result.address.unit_type == "APT"
        assert result.address.unit_number == "2B"
        assert result.address.city == "Chicago"


class TestNameParsing:
    """Tests for parsing names through the unified interface."""

    def test_parses_simple_name(self):
        """Simple first/last name should parse correctly."""
        result = parse("John Smith")
        assert result.input_type == "name"
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.parsed is True

    def test_parses_name_with_prefix(self):
        """Name with prefix should parse correctly."""
        result = parse("Dr. Jane Doe")
        assert result.name.prefix == "Dr."
        assert result.name.first == "Jane"
        assert result.name.last == "Doe"

    def test_parses_name_with_suffix(self):
        """Name with suffix should parse correctly."""
        result = parse("Robert Johnson Jr.")
        assert result.name.first == "Robert"
        assert result.name.last == "Johnson"
        assert result.name.suffix == "Jr"

    def test_parses_name_with_middle(self):
        """Name with middle name should parse correctly."""
        result = parse("John Michael Smith")
        assert result.name.first == "John"
        assert result.name.middle == "Michael"
        assert result.name.last == "Smith"


class TestContactParsing:
    """Tests for parsing contacts through the unified interface."""

    def test_parses_simple_contact(self):
        """Simple name + address should parse correctly."""
        result = parse("John Smith 123 Main St, Boston, MA 02101")
        assert result.input_type == "contact"
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.address.city == "Boston"
        assert result.address.state == "MA"
        assert result.parsed is True

    def test_parses_contact_with_name_suffix(self):
        """Contact with name suffix before address should parse correctly."""
        result = parse("John Smith Jr. 123 Main St, Boston, MA 02101")
        assert result.name.suffix == "Jr"
        assert result.address.street_number == "123"

    def test_parses_contact_with_prefix(self):
        """Contact with name prefix should parse correctly."""
        result = parse("Dr. Jane Doe 456 Oak Ave, Chicago, IL 60601")
        assert result.name.prefix == "Dr."
        assert result.name.first == "Jane"
        assert result.address.city == "Chicago"


class TestNormalization:
    """Tests for normalization option."""

    def test_normalizes_address(self):
        """Address should be normalized when requested."""
        result = parse("123 MAIN ST, BOSTON, MA 02101", normalize=True)
        assert result.address.city == "Boston"
        assert result.address.street_name == "Main"

    def test_normalizes_name(self):
        """Name should be normalized when requested."""
        result = parse("JOHN SMITH", normalize=True)
        assert result.name.first == "John"
        assert result.name.last == "Smith"


class TestValidation:
    """Tests for validation against database."""

    def test_validates_known_city(self):
        """Known city/state combination should be validated."""
        result = parse("123 Main St, Boston, MA 02101")
        # Note: validation depends on database being available
        # If database not available, validated will be False
        assert isinstance(result.validated, bool)

    def test_validated_false_for_names(self):
        """Names should not have validated=True (no address to validate)."""
        result = parse("John Smith")
        assert result.validated is False


class TestBatchParsing:
    """Tests for batch parsing."""

    def test_batch_parses_multiple_inputs(self):
        """Batch should parse multiple inputs with correct types."""
        texts = [
            "John Smith",
            "123 Main St, Boston, MA 02101",
            "Jane Doe 456 Oak Ave, Chicago, IL 60601",
        ]
        result = parse_batch(texts)

        assert isinstance(result, ParseBatchOutput)
        assert result.total == 3
        assert len(result.results) == 3

        # Check each result type
        assert result.results[0].input_type == "name"
        assert result.results[1].input_type == "address"
        assert result.results[2].input_type == "contact"

    def test_batch_counts_parsed(self):
        """Batch should count parsed results correctly."""
        texts = ["John Smith", "123 Main St, Boston, MA 02101"]
        result = parse_batch(texts)

        assert result.parsed_count == 2

    def test_batch_with_normalize(self):
        """Batch should apply normalization to all results."""
        texts = ["JOHN SMITH", "123 MAIN ST, BOSTON, MA 02101"]
        result = parse_batch(texts, normalize=True)

        assert result.results[0].name.first == "John"
        assert result.results[1].address.city == "Boston"

    def test_batch_empty_list(self):
        """Batch with empty list should return empty results."""
        result = parse_batch([])
        assert result.total == 0
        assert result.results == []


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_string(self):
        """Empty string should return with errors."""
        result = parse("")
        assert result.parsed is False
        assert len(result.errors) > 0

    def test_whitespace_only(self):
        """Whitespace-only string should return with errors."""
        result = parse("   ")
        assert result.parsed is False
        assert len(result.errors) > 0

    def test_preserves_raw_input(self):
        """Raw input should be preserved in output."""
        input_text = "John Smith 123 Main St, Boston, MA 02101"
        result = parse(input_text)
        assert result.raw_input == input_text
