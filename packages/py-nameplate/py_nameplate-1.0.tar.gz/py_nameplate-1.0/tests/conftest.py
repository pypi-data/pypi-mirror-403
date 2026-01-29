"""
Pytest configuration and shared fixtures for nameplate tests.

This module provides common fixtures used across all test modules,
including sample data, mock objects, and test utilities.

Fixtures:
    sample_addresses: Common address strings for testing
    sample_names: Common name strings for testing
    sample_contacts: Common contact strings for testing
    address_edge_cases: Edge case addresses for robustness testing
    name_edge_cases: Edge case names for robustness testing
"""

import pytest

# =============================================================================
# ADDRESS FIXTURES
# =============================================================================


@pytest.fixture
def sample_addresses() -> list[dict]:
    """
    Common US address test cases with expected parsing results.

    Returns:
        List of dicts with 'input' and expected field values
    """
    return [
        # Standard street address
        {
            "input": "123 Main St, Boston, MA 02101",
            "street_number": "123",
            "street_name": "Main",
            "street_type": "St",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02101",
            "parse_type": "Street Address",
        },
        # Address with apartment
        {
            "input": "456 Oak Avenue Apt 2B, Chicago, IL 60601",
            "street_number": "456",
            "street_name": "Oak",
            "street_type": "Avenue",
            "unit_type": "Apt",
            "unit_number": "2B",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601",
            "parse_type": "Street Address",
        },
        # PO Box
        {
            "input": "PO Box 789, Miami, FL 33101",
            "po_box": "789",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33101",
            "parse_type": "PO Box",
        },
        # Address with directional
        {
            "input": "100 N Main Street, Denver, CO 80202",
            "street_number": "100",
            "street_direction": "N",
            "street_name": "Main",
            "street_type": "Street",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80202",
            "parse_type": "Street Address",
        },
        # ZIP+4 format
        {
            "input": "200 Broadway, New York, NY 10001-1234",
            "street_number": "200",
            "street_name": "Broadway",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001-1234",
            "parse_type": "Street Address",
        },
    ]


@pytest.fixture
def address_edge_cases() -> list[dict]:
    """
    Edge case addresses for robustness testing.

    Returns:
        List of dicts with 'input' and expected behavior
    """
    return [
        # Multi-word street name
        {
            "input": "123 Martin Luther King Jr Blvd, Atlanta, GA 30301",
            "street_name": "Martin Luther King Jr",
            "street_type": "Blvd",
            "city": "Atlanta",
            "state": "GA",
        },
        # Suite instead of Apt
        {
            "input": "500 Corporate Dr Suite 100, Houston, TX 77001",
            "unit_type": "Suite",
            "unit_number": "100",
            "city": "Houston",
            "state": "TX",
        },
        # Rural route
        {
            "input": "RR 2 Box 45, Springfield, MO 65801",
            "rural_route": "2",
            "rural_box": "45",
            "city": "Springfield",
            "state": "MO",
            "parse_type": "Rural Route",
        },
        # Highway address
        {
            "input": "12345 Highway 101, San Jose, CA 95101",
            "street_number": "12345",
            "street_name": "Highway 101",
            "city": "San Jose",
            "state": "CA",
        },
        # Post-directional
        {
            "input": "789 Oak St NW, Washington, DC 20001",
            "street_number": "789",
            "street_name": "Oak",
            "street_type": "St",
            "street_direction": "NW",
            "city": "Washington",
            "state": "DC",
        },
    ]


@pytest.fixture
def invalid_addresses() -> list[str]:
    """
    Invalid or unparseable address strings.

    Returns:
        List of address strings that should fail to parse completely
    """
    return [
        "",  # Empty
        "   ",  # Whitespace only
        "Not an address at all",  # No address components
        "123",  # Just a number
        "Boston, MA",  # Missing street
    ]


# =============================================================================
# NAME FIXTURES
# =============================================================================


@pytest.fixture
def sample_names() -> list[dict]:
    """
    Common name test cases with expected parsing results.

    Returns:
        List of dicts with 'input' and expected field values
    """
    return [
        # Simple first last
        {
            "input": "John Smith",
            "first": "John",
            "last": "Smith",
        },
        # With prefix
        {
            "input": "Dr. John Smith",
            "prefix": "Dr.",
            "first": "John",
            "last": "Smith",
        },
        # With suffix
        {
            "input": "John Smith Jr.",
            "first": "John",
            "last": "Smith",
            "suffix": "Jr.",
        },
        # With middle name
        {
            "input": "John Michael Smith",
            "first": "John",
            "middle": "Michael",
            "last": "Smith",
        },
        # Last, First format
        {
            "input": "Smith, John",
            "first": "John",
            "last": "Smith",
        },
        # With nickname
        {
            "input": 'Robert "Bob" Smith',
            "first": "Robert",
            "nickname": "Bob",
            "last": "Smith",
        },
    ]


@pytest.fixture
def name_edge_cases() -> list[dict]:
    """
    Edge case names for robustness testing.

    Returns:
        List of dicts with 'input' and expected behavior
    """
    return [
        # Name particle (Dutch)
        {
            "input": "Ludwig van Beethoven",
            "first": "Ludwig",
            "last": "van Beethoven",
        },
        # Name particle (Spanish)
        {
            "input": "Juan de la Vega",
            "first": "Juan",
            "last": "de la Vega",
        },
        # Multiple prefixes
        {
            "input": "Dr. Rev. Martin Luther King Jr.",
            "prefix": "Dr. Rev.",
            "first": "Martin",
            "middle": "Luther",
            "last": "King",
            "suffix": "Jr.",
        },
        # Roman numeral suffix
        {
            "input": "Henry Ford III",
            "first": "Henry",
            "last": "Ford",
            "suffix": "III",
        },
        # Professional suffix
        {
            "input": "Jane Smith MD",
            "first": "Jane",
            "last": "Smith",
            "suffix": "MD",
        },
        # Hyphenated last name
        {
            "input": "Mary Jane Watson-Parker",
            "first": "Mary",
            "middle": "Jane",
            "last": "Watson-Parker",
        },
        # O'Name pattern
        {
            "input": "Patrick O'Brien",
            "first": "Patrick",
            "last": "O'Brien",
        },
        # McDonald pattern
        {
            "input": "Ronald McDonald",
            "first": "Ronald",
            "last": "McDonald",
        },
    ]


@pytest.fixture
def invalid_names() -> list[str]:
    """
    Invalid or empty name strings.

    Returns:
        List of name strings that should fail to parse
    """
    return [
        "",  # Empty
        "   ",  # Whitespace only
    ]


# =============================================================================
# CONTACT FIXTURES
# =============================================================================


@pytest.fixture
def sample_contacts() -> list[dict]:
    """
    Common contact (name + address) test cases.

    Returns:
        List of dicts with 'input' and expected field values
    """
    return [
        {
            "input": "John Smith 123 Main St, Boston, MA 02101",
            "name_first": "John",
            "name_last": "Smith",
            "address_city": "Boston",
            "address_state": "MA",
        },
        {
            "input": "Dr. Jane Doe 456 Oak Ave, Chicago, IL 60601",
            "name_prefix": "Dr.",
            "name_first": "Jane",
            "name_last": "Doe",
            "address_city": "Chicago",
            "address_state": "IL",
        },
        {
            "input": "Juan de la Vega PO Box 789, Miami, FL 33101",
            "name_first": "Juan",
            "name_last": "de la Vega",
            "address_city": "Miami",
            "address_state": "FL",
        },
    ]


@pytest.fixture
def contact_edge_cases() -> list[dict]:
    """
    Edge case contacts for robustness testing.

    Returns:
        List of dicts with 'input' and expected behavior
    """
    return [
        # Name with suffix before address
        {
            "input": "John Smith Jr. 123 Main St, Boston, MA 02101",
            "name_first": "John",
            "name_last": "Smith",
            "name_suffix": "Jr.",
            "address_street_number": "123",
        },
        # Name with Roman numeral suffix (tricky - looks like number)
        {
            "input": "Henry Ford III 100 Auto Dr, Detroit, MI 48201",
            "name_first": "Henry",
            "name_last": "Ford",
            "name_suffix": "III",
            "address_street_number": "100",
        },
    ]


# =============================================================================
# UTILITY FIXTURES
# =============================================================================


@pytest.fixture
def normalize_test_cases() -> list[dict]:
    """
    Test cases for normalization functionality.

    Returns:
        List of dicts with input and expected normalized output
    """
    return [
        {"input": "JOHN SMITH", "expected": "John Smith"},
        {"input": "john smith", "expected": "John Smith"},
        {"input": "mcdonald", "expected": "McDonald"},
        {"input": "o'brien", "expected": "O'Brien"},
        {"input": "VAN BEETHOVEN", "expected": "van Beethoven"},
    ]
