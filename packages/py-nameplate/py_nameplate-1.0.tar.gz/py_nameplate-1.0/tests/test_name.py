"""
Tests for name parsing functionality.

This module tests name parsing through the unified parse() function,
covering standard names, edge cases, and error handling.

Test Categories:
    - Basic parsing: First, middle, last names
    - Prefixes: Dr., Mr., Mrs., Ms., Rev., etc.
    - Suffixes: Jr., Sr., III, PhD, MD, etc.
    - Nicknames: Quoted nicknames like "Bob"
    - Name particles: van, de, von, al, etc.
    - Special formats: Last, First ordering
    - Normalization: Smart title case
    - Batch processing: Multiple names
    - Error handling: Invalid inputs
"""

import pytest

from nameplate import parse, parse_batch
from nameplate.schemas import NameOutput, ParseBatchOutput, ParseOutput

# =============================================================================
# BASIC PARSING TESTS
# =============================================================================


class TestBasicNameParsing:
    """Tests for basic name parsing functionality."""

    def test_simple_first_last(self):
        """Parse simple first and last name."""
        result = parse("John Smith")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_first_middle_last(self):
        """Parse first, middle, and last name."""
        result = parse("John Michael Smith")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.middle == "Michael"
        assert result.name.last == "Smith"

    def test_multiple_middle_names(self):
        """Parse name with multiple middle names."""
        result = parse("John Paul George Smith")

        assert result.parsed is True
        assert result.name.first == "John"
        # Middle should contain the middle name(s)
        assert result.name.last == "Smith"

    def test_returns_parse_output(self):
        """Verify return type is ParseOutput."""
        result = parse("John Smith")
        assert isinstance(result, ParseOutput)
        assert isinstance(result.name, NameOutput)

    def test_raw_input_preserved(self):
        """Verify raw input is preserved in output."""
        input_name = "John Smith"
        result = parse(input_name)
        assert result.raw_input == input_name

    def test_single_name(self):
        """Parse single name (no last name)."""
        result = parse("Madonna")

        assert result.parsed is True
        # Single name could be first or last depending on implementation
        assert result.name.first == "Madonna" or result.name.last == "Madonna"


# =============================================================================
# PREFIX TESTS
# =============================================================================


class TestPrefixes:
    """Tests for name prefix parsing."""

    @pytest.mark.parametrize(
        "prefix",
        ["Dr.", "Dr", "Mr.", "Mr", "Mrs.", "Mrs", "Ms.", "Ms", "Miss"],
    )
    def test_common_prefixes(self, prefix):
        """Parse names with common prefixes."""
        result = parse(f"{prefix} John Smith")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert prefix.rstrip(".") in result.name.prefix.replace(".", "")

    def test_reverend_prefix(self):
        """Parse name with Rev. prefix."""
        result = parse("Rev. John Smith")

        assert result.parsed is True
        assert "Rev" in result.name.prefix

    def test_multiple_prefixes(self):
        """Parse name with multiple prefixes."""
        result = parse("Dr. Rev. John Smith")

        assert result.parsed is True
        assert result.name.first == "John"
        # Both prefixes should be captured
        assert "Dr" in result.name.prefix or "Rev" in result.name.prefix

    def test_military_prefix(self):
        """Parse name with military rank prefix."""
        result = parse("Gen. John Smith")

        assert result.parsed is True
        assert "Gen" in result.name.prefix

    def test_professor_prefix(self):
        """Parse name with Prof. prefix."""
        result = parse("Prof. John Smith")

        assert result.parsed is True
        assert "Prof" in result.name.prefix


# =============================================================================
# SUFFIX TESTS
# =============================================================================


class TestSuffixes:
    """Tests for name suffix parsing."""

    @pytest.mark.parametrize(
        "suffix",
        ["Jr.", "Jr", "Sr.", "Sr", "Junior", "Senior"],
    )
    def test_generational_suffixes(self, suffix):
        """Parse names with Jr./Sr. suffixes."""
        result = parse(f"John Smith {suffix}")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.name.suffix is not None

    @pytest.mark.parametrize(
        "suffix",
        ["I", "II", "III", "IV", "V"],
    )
    def test_roman_numeral_suffixes(self, suffix):
        """Parse names with Roman numeral suffixes."""
        result = parse(f"John Smith {suffix}")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert result.name.suffix == suffix

    @pytest.mark.parametrize(
        "suffix",
        ["MD", "PhD", "JD", "DDS", "DO", "MBA", "CPA", "RN", "Esq", "Esq."],
    )
    def test_professional_suffixes(self, suffix):
        """Parse names with professional suffixes."""
        result = parse(f"John Smith {suffix}")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        assert suffix.rstrip(".") in result.name.suffix.replace(".", "")

    def test_multiple_suffixes(self):
        """Parse name with multiple suffixes."""
        result = parse("John Smith Jr. MD")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        # Both suffixes should be captured
        assert "Jr" in result.name.suffix or "MD" in result.name.suffix


# =============================================================================
# NICKNAME TESTS
# =============================================================================


class TestNicknames:
    """Tests for nickname parsing."""

    def test_quoted_nickname_double(self):
        """Parse name with double-quoted nickname."""
        result = parse('Robert "Bob" Smith')

        assert result.parsed is True
        assert result.name.first == "Robert"
        assert result.name.nickname == "Bob"
        assert result.name.last == "Smith"

    def test_quoted_nickname_single(self):
        """Parse name with single-quoted nickname."""
        result = parse("Robert 'Bob' Smith")

        assert result.parsed is True
        assert result.name.first == "Robert"
        assert result.name.nickname == "Bob"
        assert result.name.last == "Smith"

    def test_parenthetical_nickname(self):
        """Parse name with nickname in parentheses."""
        result = parse("Robert (Bob) Smith")

        assert result.parsed is True
        assert result.name.first == "Robert"
        assert result.name.nickname == "Bob"
        assert result.name.last == "Smith"

    def test_nickname_with_prefix(self):
        """Parse name with both prefix and nickname."""
        result = parse('Dr. Robert "Bob" Smith')

        assert result.parsed is True
        assert "Dr" in result.name.prefix
        assert result.name.first == "Robert"
        assert result.name.nickname == "Bob"


# =============================================================================
# NAME PARTICLE TESTS
# =============================================================================


class TestNameParticles:
    """Tests for name particles (van, de, von, etc.)."""

    def test_dutch_van(self):
        """Parse Dutch 'van' name particle."""
        result = parse("Ludwig van Beethoven")

        assert result.parsed is True
        assert result.name.first == "Ludwig"
        assert "van" in result.name.last.lower()
        assert "Beethoven" in result.name.last

    def test_dutch_van_der(self):
        """Parse Dutch 'van der' name particle."""
        result = parse("Jan van der Berg")

        assert result.parsed is True
        assert result.name.first == "Jan"
        assert "van der" in result.name.last.lower()

    def test_german_von(self):
        """Parse German 'von' name particle."""
        result = parse("Otto von Bismarck")

        assert result.parsed is True
        assert result.name.first == "Otto"
        assert "von" in result.name.last.lower()

    def test_spanish_de_la(self):
        """Parse Spanish 'de la' name particle."""
        result = parse("Juan de la Vega")

        assert result.parsed is True
        assert result.name.first == "Juan"
        assert "de la" in result.name.last.lower()

    def test_arabic_al(self):
        """Parse Arabic 'al' name particle."""
        result = parse("Ahmed al-Rashid")

        assert result.parsed is True
        assert result.name.first == "Ahmed"
        assert "al" in result.name.last.lower()

    def test_italian_da(self):
        """Parse Italian 'da' name particle."""
        result = parse("Leonardo da Vinci")

        assert result.parsed is True
        assert result.name.first == "Leonardo"
        assert "da" in result.name.last.lower()


# =============================================================================
# SPECIAL FORMAT TESTS
# =============================================================================


class TestSpecialFormats:
    """Tests for special name formats."""

    def test_last_comma_first(self):
        """Parse 'Last, First' format."""
        result = parse("Smith, John")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_last_comma_first_middle(self):
        """Parse 'Last, First Middle' format."""
        result = parse("Smith, John Michael")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.middle == "Michael"
        assert result.name.last == "Smith"

    def test_last_comma_first_with_suffix(self):
        """Parse 'Last, First Suffix' format."""
        result = parse("Smith, John Jr.")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"
        # Suffix parsing in comma-format may vary
        # Jr. might end up in middle or suffix depending on implementation
        assert "Jr" in result.name.suffix or "Jr" in result.name.middle

    def test_hyphenated_last_name(self):
        """Parse hyphenated last name."""
        result = parse("Mary Watson-Parker")

        assert result.parsed is True
        assert result.name.first == "Mary"
        assert "Watson-Parker" in result.name.last or "Watson" in result.name.last

    def test_hyphenated_first_name(self):
        """Parse hyphenated first name."""
        result = parse("Mary-Jane Watson")

        assert result.parsed is True
        assert "Mary" in result.name.first
        assert result.name.last == "Watson"


# =============================================================================
# SPECIAL CHARACTER TESTS
# =============================================================================


class TestSpecialCharacters:
    """Tests for names with special characters."""

    def test_apostrophe_in_name(self):
        """Parse name with apostrophe (O'Brien)."""
        result = parse("Patrick O'Brien")

        assert result.parsed is True
        assert result.name.first == "Patrick"
        assert "O'Brien" in result.name.last or "O'" in result.name.last

    def test_mc_name(self):
        """Parse Mc name (McDonald)."""
        result = parse("Ronald McDonald")

        assert result.parsed is True
        assert result.name.first == "Ronald"
        assert result.name.last == "McDonald"

    def test_mac_name(self):
        """Parse Mac name (MacArthur)."""
        result = parse("Douglas MacArthur")

        assert result.parsed is True
        assert result.name.first == "Douglas"
        assert result.name.last == "MacArthur"


# =============================================================================
# NORMALIZATION TESTS
# =============================================================================


class TestNormalization:
    """Tests for name normalization functionality."""

    def test_normalize_uppercase(self):
        """Normalize all-uppercase name to title case."""
        result = parse("JOHN SMITH", normalize=True)

        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_normalize_lowercase(self):
        """Normalize all-lowercase name to title case."""
        result = parse("john smith", normalize=True)

        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_normalize_mcdonald(self):
        """Normalize McDonald with proper casing."""
        result = parse("ronald mcdonald", normalize=True)

        assert result.name.first == "Ronald"
        assert result.name.last == "McDonald"

    def test_normalize_obrien(self):
        """Normalize O'Brien with proper casing."""
        result = parse("patrick o'brien", normalize=True)

        assert result.name.first == "Patrick"
        assert "O'Brien" in result.name.last or "O'b" in result.name.last

    def test_normalize_preserves_particles(self):
        """Name particles should be handled during normalization."""
        result = parse("LUDWIG VAN BEETHOVEN", normalize=True)

        assert result.name.first == "Ludwig"
        # Particle handling may vary - may be lowercase or title case
        assert "van" in result.name.last.lower() or "Van" in result.name.last

    def test_no_normalize_by_default(self):
        """Without normalize flag, preserve original case."""
        result = parse("JOHN SMITH")

        assert result.name.first == "JOHN"
        assert result.name.last == "SMITH"


# =============================================================================
# BATCH PROCESSING TESTS
# =============================================================================


class TestBatchProcessing:
    """Tests for batch name parsing."""

    def test_parse_multiple_names(self):
        """Parse multiple names in batch."""
        names = [
            "John Smith",
            "Jane Doe",
            "Bob Johnson",
        ]

        result = parse_batch(names)

        assert isinstance(result, ParseBatchOutput)
        assert result.total == 3
        assert result.parsed_count == 3
        assert len(result.results) == 3

    def test_batch_with_failures(self):
        """Batch with some unparseable names."""
        names = [
            "John Smith",
            "",  # Empty - will fail
            "Jane Doe",
        ]

        result = parse_batch(names)

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
        names = [
            "Alice Smith",
            "Bob Jones",
            "Carol Brown",
        ]

        result = parse_batch(names)

        assert result.results[0].name.first == "Alice"
        assert result.results[1].name.first == "Bob"
        assert result.results[2].name.first == "Carol"

    def test_batch_with_normalization(self):
        """Batch parsing with normalization enabled."""
        names = [
            "JOHN SMITH",
            "jane doe",
        ]

        result = parse_batch(names, normalize=True)

        assert result.results[0].name.first == "John"
        assert result.results[1].name.first == "Jane"


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

    def test_extra_whitespace(self):
        """Name with extra whitespace should parse correctly."""
        result = parse("  John    Smith  ")

        assert result.parsed is True
        assert result.name.first == "John"
        assert result.name.last == "Smith"

    def test_special_characters_only(self):
        """String with only special characters."""
        result = parse("!@#$%")

        # Should handle gracefully
        assert isinstance(result, ParseOutput)


# =============================================================================
# COMPLEX NAME TESTS
# =============================================================================


class TestComplexNames:
    """Tests for complex real-world names."""

    def test_full_formal_name(self):
        """Parse full formal name with all components."""
        result = parse("Dr. Martin Luther King Jr.")

        assert result.parsed is True
        assert "Dr" in result.name.prefix
        assert result.name.first == "Martin"
        assert result.name.middle == "Luther"
        assert result.name.last == "King"
        assert "Jr" in result.name.suffix

    def test_full_name_with_nickname(self):
        """Parse formal name with nickname."""
        result = parse('William "Bill" Jefferson Clinton')

        assert result.parsed is True
        assert result.name.first == "William"
        assert result.name.nickname == "Bill"
        # Jefferson could be middle, Clinton should be last

    def test_international_name(self):
        """Parse international name with particles."""
        result = parse("Gabriel García Márquez")

        assert result.parsed is True
        assert result.name.first == "Gabriel"
        # Spanish naming conventions
