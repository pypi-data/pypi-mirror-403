"""
Tests for Pydantic schema models.

This module tests the input and output schema definitions,
ensuring proper validation, serialization, and default values.

Test Categories:
    - Input schemas: AddressInput, NameInput, ContactInput
    - Output schemas: AddressOutput, NameOutput, ContactOutput
    - Batch schemas: Batch variants of all above
    - Serialization: JSON serialization and deserialization
    - Validation: Field validation and constraints
"""

import pytest
from pydantic import ValidationError

from nameplate.schemas import (
    AddressBatchInput,
    AddressBatchOutput,
    # Input schemas
    AddressInput,
    # Output schemas
    AddressOutput,
    ContactBatchInput,
    ContactBatchOutput,
    ContactInput,
    ContactOutput,
    NameBatchInput,
    NameBatchOutput,
    NameInput,
    NameOutput,
)

# =============================================================================
# ADDRESS INPUT TESTS
# =============================================================================


class TestAddressInput:
    """Tests for AddressInput schema."""

    def test_basic_creation(self):
        """Create AddressInput with required fields."""
        input_schema = AddressInput(address="123 Main St, Boston, MA 02101")

        assert input_schema.address == "123 Main St, Boston, MA 02101"
        assert input_schema.normalize is False  # Default
        assert input_schema.enhance is False  # Default

    def test_with_options(self):
        """Create AddressInput with optional flags."""
        input_schema = AddressInput(
            address="123 Main St, Boston, MA 02101",
            normalize=True,
            enhance=True,
        )

        assert input_schema.normalize is True
        assert input_schema.enhance is True

    def test_json_schema_generation(self):
        """Verify JSON schema can be generated."""
        schema = AddressInput.model_json_schema()

        assert "properties" in schema
        assert "address" in schema["properties"]

    def test_empty_address_allowed(self):
        """Empty address string should be allowed (validation happens in parser)."""
        input_schema = AddressInput(address="")
        assert input_schema.address == ""


# =============================================================================
# NAME INPUT TESTS
# =============================================================================


class TestNameInput:
    """Tests for NameInput schema."""

    def test_basic_creation(self):
        """Create NameInput with required fields."""
        input_schema = NameInput(name="John Smith")

        assert input_schema.name == "John Smith"
        assert input_schema.normalize is False  # Default

    def test_with_normalize(self):
        """Create NameInput with normalize flag."""
        input_schema = NameInput(name="john smith", normalize=True)

        assert input_schema.normalize is True

    def test_json_schema_generation(self):
        """Verify JSON schema can be generated."""
        schema = NameInput.model_json_schema()

        assert "properties" in schema
        assert "name" in schema["properties"]


# =============================================================================
# CONTACT INPUT TESTS
# =============================================================================


class TestContactInput:
    """Tests for ContactInput schema."""

    def test_basic_creation(self):
        """Create ContactInput with required fields."""
        input_schema = ContactInput(text="John Smith 123 Main St, Boston, MA 02101")

        assert input_schema.text == "John Smith 123 Main St, Boston, MA 02101"
        assert input_schema.normalize is False
        assert input_schema.enhance is False

    def test_with_options(self):
        """Create ContactInput with optional flags."""
        input_schema = ContactInput(
            text="John Smith 123 Main St, Boston, MA 02101",
            normalize=True,
            enhance=True,
        )

        assert input_schema.normalize is True
        assert input_schema.enhance is True


# =============================================================================
# ADDRESS OUTPUT TESTS
# =============================================================================


class TestAddressOutput:
    """Tests for AddressOutput schema."""

    def test_basic_creation(self):
        """Create AddressOutput with minimal fields."""
        output = AddressOutput(raw_input="123 Main St, Boston, MA 02101")

        assert output.raw_input == "123 Main St, Boston, MA 02101"
        assert output.parsed is False  # Default
        assert output.errors == []  # Default empty list

    def test_full_address(self):
        """Create AddressOutput with all address fields."""
        output = AddressOutput(
            raw_input="123 Main St Apt 4, Boston, MA 02101",
            street_number="123",
            street_name="Main",
            street_type="St",
            unit_type="Apt",
            unit_number="4",
            city="Boston",
            state="MA",
            zip_code="02101",
            parsed=True,
            parse_type="Street Address",
        )

        assert output.street_number == "123"
        assert output.street_name == "Main"
        assert output.unit_type == "Apt"
        assert output.parsed is True

    def test_po_box_address(self):
        """Create AddressOutput for PO Box."""
        # Note: PO Box info is stored in street_name field
        output = AddressOutput(
            raw_input="PO Box 123, Miami, FL 33101",
            street_name="PO Box 123",
            city="Miami",
            state="FL",
            zip_code="33101",
            parsed=True,
            parse_type="PO Box",
        )

        assert output.street_name == "PO Box 123"
        assert output.parse_type == "PO Box"

    def test_json_serialization(self):
        """Verify output can be serialized to JSON."""
        output = AddressOutput(
            raw_input="123 Main St, Boston, MA 02101",
            city="Boston",
            state="MA",
            parsed=True,
        )

        json_str = output.model_dump_json()
        assert "Boston" in json_str
        assert "MA" in json_str

    def test_model_dump(self):
        """Verify output can be converted to dict."""
        output = AddressOutput(
            raw_input="123 Main St, Boston, MA 02101",
            city="Boston",
        )

        data = output.model_dump()
        assert isinstance(data, dict)
        assert data["city"] == "Boston"


# =============================================================================
# NAME OUTPUT TESTS
# =============================================================================


class TestNameOutput:
    """Tests for NameOutput schema."""

    def test_basic_creation(self):
        """Create NameOutput with minimal fields."""
        output = NameOutput(raw_input="John Smith")

        assert output.raw_input == "John Smith"
        assert output.parsed is False  # Default
        assert output.errors == []

    def test_full_name(self):
        """Create NameOutput with all name fields."""
        output = NameOutput(
            raw_input="Dr. John Michael Smith Jr.",
            prefix="Dr.",
            first="John",
            middle="Michael",
            last="Smith",
            suffix="Jr.",
            parsed=True,
        )

        assert output.prefix == "Dr."
        assert output.first == "John"
        assert output.middle == "Michael"
        assert output.last == "Smith"
        assert output.suffix == "Jr."

    def test_with_nickname(self):
        """Create NameOutput with nickname."""
        output = NameOutput(
            raw_input='Robert "Bob" Smith',
            first="Robert",
            nickname="Bob",
            last="Smith",
            parsed=True,
        )

        assert output.nickname == "Bob"

    def test_json_serialization(self):
        """Verify output can be serialized to JSON."""
        output = NameOutput(
            raw_input="John Smith",
            first="John",
            last="Smith",
            parsed=True,
        )

        json_str = output.model_dump_json()
        assert "John" in json_str
        assert "Smith" in json_str


# =============================================================================
# CONTACT OUTPUT TESTS
# =============================================================================


class TestContactOutput:
    """Tests for ContactOutput schema."""

    def test_basic_creation(self):
        """Create ContactOutput with minimal fields."""
        output = ContactOutput(raw_input="John Smith 123 Main St, Boston, MA 02101")

        assert output.raw_input == "John Smith 123 Main St, Boston, MA 02101"
        assert output.parsed is False
        assert output.errors == []

    def test_with_name_and_address(self):
        """Create ContactOutput with nested name and address."""
        name = NameOutput(
            raw_input="John Smith",
            first="John",
            last="Smith",
            parsed=True,
        )
        address = AddressOutput(
            raw_input="123 Main St, Boston, MA 02101",
            street_number="123",
            city="Boston",
            state="MA",
            parsed=True,
        )

        output = ContactOutput(
            raw_input="John Smith 123 Main St, Boston, MA 02101",
            name=name,
            address=address,
            split_index=11,
            parsed=True,
        )

        assert output.name.first == "John"
        assert output.address.city == "Boston"
        assert output.split_index == 11

    def test_json_serialization(self):
        """Verify output can be serialized to JSON."""
        output = ContactOutput(
            raw_input="John Smith 123 Main St, Boston, MA 02101",
            parsed=True,
        )

        json_str = output.model_dump_json()
        assert "John Smith" in json_str


# =============================================================================
# BATCH INPUT TESTS
# =============================================================================


class TestBatchInputSchemas:
    """Tests for batch input schemas."""

    def test_address_batch_input(self):
        """Create AddressBatchInput with list of addresses."""
        batch = AddressBatchInput(
            addresses=[
                "123 Main St, Boston, MA 02101",
                "456 Oak Ave, Chicago, IL 60601",
            ]
        )

        assert len(batch.addresses) == 2
        assert batch.normalize is False

    def test_name_batch_input(self):
        """Create NameBatchInput with list of names."""
        batch = NameBatchInput(
            names=["John Smith", "Jane Doe"],
            normalize=True,
        )

        assert len(batch.names) == 2
        assert batch.normalize is True

    def test_contact_batch_input(self):
        """Create ContactBatchInput with list of contacts."""
        batch = ContactBatchInput(
            contacts=[
                "John Smith 123 Main St, Boston, MA 02101",
                "Jane Doe 456 Oak Ave, Chicago, IL 60601",
            ]
        )

        assert len(batch.contacts) == 2

    def test_empty_batch_allowed(self):
        """Empty batch should be allowed."""
        batch = AddressBatchInput(addresses=[])
        assert len(batch.addresses) == 0


# =============================================================================
# BATCH OUTPUT TESTS
# =============================================================================


class TestBatchOutputSchemas:
    """Tests for batch output schemas."""

    def test_address_batch_output(self):
        """Create AddressBatchOutput with results."""
        result1 = AddressOutput(raw_input="addr1", parsed=True)
        result2 = AddressOutput(raw_input="addr2", parsed=False)

        batch = AddressBatchOutput(
            results=[result1, result2],
            total=2,
            parsed_count=1,
            validated_count=0,
        )

        assert batch.total == 2
        assert batch.parsed_count == 1
        assert len(batch.results) == 2

    def test_name_batch_output(self):
        """Create NameBatchOutput with results."""
        result1 = NameOutput(raw_input="name1", parsed=True)
        result2 = NameOutput(raw_input="name2", parsed=True)

        batch = NameBatchOutput(
            results=[result1, result2],
            total=2,
            parsed_count=2,
        )

        assert batch.total == 2
        assert batch.parsed_count == 2

    def test_contact_batch_output(self):
        """Create ContactBatchOutput with results."""
        result = ContactOutput(raw_input="contact1", parsed=True)

        batch = ContactBatchOutput(
            results=[result],
            total=1,
            parsed_count=1,
            validated_count=0,
        )

        assert batch.total == 1

    def test_batch_json_serialization(self):
        """Verify batch output can be serialized to JSON."""
        batch = AddressBatchOutput(
            results=[],
            total=0,
            parsed_count=0,
            validated_count=0,
        )

        json_str = batch.model_dump_json()
        assert "total" in json_str
        assert "results" in json_str


# =============================================================================
# SCHEMA DEFAULTS TESTS
# =============================================================================


class TestSchemaDefaults:
    """Tests for schema default values."""

    def test_address_output_defaults(self):
        """AddressOutput should have sensible defaults."""
        output = AddressOutput(raw_input="test")

        # Fields default to empty string, not None
        assert output.street_number == ""
        assert output.street_name == ""
        assert output.city == ""
        assert output.state == ""
        assert output.zip_code == ""
        assert output.parsed is False
        assert output.validated is False
        assert output.enhanced is False
        assert output.errors == []

    def test_name_output_defaults(self):
        """NameOutput should have sensible defaults."""
        output = NameOutput(raw_input="test")

        # Fields default to empty string, not None
        assert output.prefix == ""
        assert output.first == ""
        assert output.middle == ""
        assert output.last == ""
        assert output.suffix == ""
        assert output.nickname == ""
        assert output.parsed is False
        assert output.errors == []

    def test_contact_output_defaults(self):
        """ContactOutput should have sensible defaults."""
        output = ContactOutput(raw_input="test")

        # Name and address default to empty instances, not None
        assert output.name is not None
        assert output.address is not None
        assert output.split_index == -1  # Default to -1
        assert output.parsed is False
        assert output.validated is False
        assert output.enhanced is False
        assert output.errors == []


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_address_input_requires_address(self):
        """AddressInput should require address field."""
        with pytest.raises(ValidationError):
            AddressInput()  # Missing required 'address'

    def test_name_input_requires_name(self):
        """NameInput should require name field."""
        with pytest.raises(ValidationError):
            NameInput()  # Missing required 'name'

    def test_contact_input_requires_text(self):
        """ContactInput should require text field."""
        with pytest.raises(ValidationError):
            ContactInput()  # Missing required 'text'

    def test_output_has_raw_input_default(self):
        """Output schemas have raw_input with empty default."""
        # raw_input has a default of "", so these should not raise
        addr = AddressOutput()
        assert addr.raw_input == ""

        name = NameOutput()
        assert name.raw_input == ""

        contact = ContactOutput()
        assert contact.raw_input == ""
