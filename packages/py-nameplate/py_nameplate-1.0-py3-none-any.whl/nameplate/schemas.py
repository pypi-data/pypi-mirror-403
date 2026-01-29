"""
Input and output schemas for nameplate parsing tools.

This module defines Pydantic models for all inputs and outputs used by the
parsing functions. These models provide:
- Input validation with clear error messages
- Type hints for IDE autocompletion
- JSON schema generation for MCP tool definitions
- Serialization to JSON for MCP responses

Model Categories:
    Input Models: Define parameters for parsing functions
        - AddressInput, NameInput, ContactInput (single item)
        - AddressBatchInput, NameBatchInput, ContactBatchInput (batch)

    Output Models: Define structure of parsing results
        - AddressOutput, NameOutput, ContactOutput (single item)
        - AddressBatchOutput, NameBatchOutput, ContactBatchOutput (batch)

Usage:
    >>> from nameplate.schemas import AddressInput, AddressOutput
    >>>
    >>> # Validate input
    >>> input = AddressInput(address="123 Main St, Boston, MA 02101")
    >>>
    >>> # Create output
    >>> output = AddressOutput(
    ...     street_number="123",
    ...     city="Boston",
    ...     state="MA",
    ...     parsed=True
    ... )
    >>>
    >>> # Serialize to JSON
    >>> output.model_dump_json(indent=2)
"""

from pydantic import BaseModel, Field

# =============================================================================
# INPUT SCHEMAS
# =============================================================================


class AddressInput(BaseModel):
    """
    Input schema for parsing a single US address.

    Attributes:
        address: The full address string to parse. Can be single or multi-line.
            Examples: "123 Main St, Boston, MA 02101"
                     "456 Oak Ave, Apt 2B, Chicago, IL 60601"
                     "PO Box 789, Miami, FL 33101"
        normalize: If True, normalize output to title case. Handles special
            cases like McDonald, O'Brien, etc. Default False preserves
            original casing from input.
        enhance: If True, attempt to fill in missing data by looking up
            city in the database to infer state. Only works for unambiguous
            cities. Default False.
    """

    address: str = Field(
        ...,
        description="Full address string to parse (e.g., '123 Main St, Boston, MA 02101')",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data (like state) from database if True",
    )


class NameInput(BaseModel):
    """
    Input schema for parsing a single full name.

    Attributes:
        name: The full name string to parse. Supports various formats:
            - Simple: "John Smith"
            - With prefix: "Dr. Jane Doe"
            - With suffix: "Robert Johnson Jr."
            - Last-first: "Smith, John"
            - With nickname: 'Robert "Bob" Smith'
        normalize: If True, normalize output to title case. Handles special
            cases like McDonald, O'Brien, MacArthur. Default False.
    """

    name: str = Field(
        ...,
        description="Full name string to parse (e.g., 'Dr. John Smith Jr.')",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )


class ContactInput(BaseModel):
    """
    Input schema for parsing a freeform string containing both name and address.

    Attributes:
        text: Freeform string containing name followed by address.
            Example: "John Smith 123 Main St, Boston, MA 02101"
        normalize: If True, normalize output to title case. Default False.
        enhance: If True, attempt to fill in missing address data. Default False.
    """

    text: str = Field(
        ...,
        description="Freeform string containing name and address",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data from database if True",
    )


# -----------------------------------------------------------------------------
# Batch Input Schemas
# -----------------------------------------------------------------------------


class AddressBatchInput(BaseModel):
    """
    Input schema for parsing multiple addresses in a single call.

    Use this for efficient batch processing of address lists.

    Attributes:
        addresses: List of address strings to parse.
        normalize: Apply normalization to all outputs. Default False.
        enhance: Apply enhancement to all outputs. Default False.
    """

    addresses: list[str] = Field(
        ...,
        description="Array of address strings to parse",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data from database if True",
    )


class NameBatchInput(BaseModel):
    """
    Input schema for parsing multiple names in a single call.

    Use this for efficient batch processing of name lists.

    Attributes:
        names: List of name strings to parse.
        normalize: Apply normalization to all outputs. Default False.
    """

    names: list[str] = Field(
        ...,
        description="Array of name strings to parse",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )


class ContactBatchInput(BaseModel):
    """
    Input schema for parsing multiple contact strings in a single call.

    Use this for efficient batch processing of combined name+address strings.

    Attributes:
        contacts: List of contact strings to parse.
        normalize: Apply normalization to all outputs. Default False.
        enhance: Apply enhancement to all outputs. Default False.
    """

    contacts: list[str] = Field(
        ...,
        description="Array of contact strings to parse",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data from database if True",
    )


# =============================================================================
# OUTPUT SCHEMAS
# =============================================================================


class AddressOutput(BaseModel):
    """
    Output schema for a parsed address.

    All fields are optional strings that default to empty. The `parsed` and
    `validated` flags indicate the quality of the parse result.

    Attributes:
        street_number: House or building number (e.g., "123", "456-B")
        street_name: Name of the street without type (e.g., "Main", "Oak")
        street_type: Street suffix (e.g., "St", "Ave", "Boulevard")
        street_direction: Directional prefix or suffix (e.g., "N", "SE")
        unit_type: Unit designator (e.g., "Apt", "Suite", "Unit", "#")
        unit_number: Unit or apartment number (e.g., "4B", "200")
        city: City name (e.g., "Boston", "Los Angeles")
        state: Two-letter state abbreviation (e.g., "MA", "CA")
        zip_code: ZIP code, 5 or 9 digit (e.g., "02101", "90210-1234")
        raw_input: The original input string, preserved for reference
        parsed: True if parsing succeeded (extracted at least some components)
        validated: True if city/state combination was found in database
        enhanced: True if missing data was filled in from database
        parse_type: Type of address detected ("Street Address" or "PO Box")
        errors: List of any errors or warnings during parsing
    """

    street_number: str = Field(default="", description="House/building number")
    street_name: str = Field(default="", description="Street name")
    street_type: str = Field(default="", description="St, Ave, Blvd, etc.")
    street_direction: str = Field(default="", description="N, S, E, W, NE, etc.")
    unit_type: str = Field(default="", description="Apt, Suite, Unit, etc.")
    unit_number: str = Field(default="", description="Unit/apartment number")
    city: str = Field(default="", description="City name")
    state: str = Field(default="", description="State abbreviation")
    zip_code: str = Field(default="", description="ZIP code (5 or 9 digit)")
    raw_input: str = Field(default="", description="Original input string")
    parsed: bool = Field(default=False, description="True if parsing succeeded")
    validated: bool = Field(default=False, description="True if city/state validated")
    enhanced: bool = Field(default=False, description="True if data was enhanced")
    parse_type: str = Field(default="", description="Address type detected")
    errors: list[str] = Field(default_factory=list, description="Parsing errors")


class NameOutput(BaseModel):
    """
    Output schema for a parsed name.

    All fields are optional strings that default to empty. The `parsed` flag
    indicates whether any name components were successfully extracted.

    Attributes:
        prefix: Title or honorific (e.g., "Dr.", "Mr.", "Mrs.", "Lt. Gen.")
        first: First/given name (e.g., "John", "Mary")
        middle: Middle name(s) (e.g., "Paul", "Jane Elizabeth")
        last: Last/family name (e.g., "Smith", "Garcia-Lopez", "van der Berg")
        suffix: Suffix (e.g., "Jr.", "Sr.", "III", "PhD", "MD")
        nickname: Nickname if present (e.g., "Bob" from 'Robert "Bob" Smith')
        raw_input: The original input string, preserved for reference
        parsed: True if parsing succeeded (extracted at least some components)
        errors: List of any errors or warnings during parsing
    """

    prefix: str = Field(default="", description="Title/prefix (Dr., Mr., etc.)")
    first: str = Field(default="", description="First/given name")
    middle: str = Field(default="", description="Middle name(s)")
    last: str = Field(default="", description="Last/family name")
    suffix: str = Field(default="", description="Suffix (Jr., PhD, etc.)")
    nickname: str = Field(default="", description="Nickname if present")
    raw_input: str = Field(default="", description="Original input string")
    parsed: bool = Field(default=False, description="True if parsing succeeded")
    errors: list[str] = Field(default_factory=list, description="Parsing errors")


class ContactOutput(BaseModel):
    """
    Output schema for a parsed contact (combined name and address).

    Contains nested NameOutput and AddressOutput objects, plus metadata
    about the parsing process.

    Attributes:
        name: Parsed name components (NameOutput)
        address: Parsed address components (AddressOutput)
        raw_input: The original input string, preserved for reference
        split_index: Character index where name ends and address begins
        parsed: True if both name and address were extracted
        validated: True if address city/state was validated
        enhanced: True if any data was enhanced from database
        errors: List of any errors or warnings during parsing
    """

    name: NameOutput = Field(default_factory=NameOutput, description="Parsed name")
    address: AddressOutput = Field(default_factory=AddressOutput, description="Parsed address")
    raw_input: str = Field(default="", description="Original input string")
    split_index: int = Field(default=-1, description="Index where name ends and address begins")
    parsed: bool = Field(default=False, description="True if both name and address parsed")
    validated: bool = Field(default=False, description="True if address validated")
    enhanced: bool = Field(default=False, description="True if data was enhanced")
    errors: list[str] = Field(default_factory=list, description="Parsing errors")


# -----------------------------------------------------------------------------
# Batch Output Schemas
# -----------------------------------------------------------------------------


class AddressBatchOutput(BaseModel):
    """
    Output schema for batch address parsing.

    Contains the list of individual results plus summary statistics.

    Attributes:
        results: List of AddressOutput for each input address
        total: Total number of addresses processed
        parsed_count: Number that were successfully parsed
        validated_count: Number that were validated against database
    """

    results: list[AddressOutput] = Field(default_factory=list, description="Parsed addresses")
    total: int = Field(default=0, description="Total inputs processed")
    parsed_count: int = Field(default=0, description="Successfully parsed count")
    validated_count: int = Field(default=0, description="Validated count")


class NameBatchOutput(BaseModel):
    """
    Output schema for batch name parsing.

    Contains the list of individual results plus summary statistics.

    Attributes:
        results: List of NameOutput for each input name
        total: Total number of names processed
        parsed_count: Number that were successfully parsed
    """

    results: list[NameOutput] = Field(default_factory=list, description="Parsed names")
    total: int = Field(default=0, description="Total inputs processed")
    parsed_count: int = Field(default=0, description="Successfully parsed count")


class ContactBatchOutput(BaseModel):
    """
    Output schema for batch contact parsing.

    Contains the list of individual results plus summary statistics.

    Attributes:
        results: List of ContactOutput for each input contact
        total: Total number of contacts processed
        parsed_count: Number that were successfully parsed
        validated_count: Number with validated addresses
    """

    results: list[ContactOutput] = Field(default_factory=list, description="Parsed contacts")
    total: int = Field(default=0, description="Total inputs processed")
    parsed_count: int = Field(default=0, description="Successfully parsed count")
    validated_count: int = Field(default=0, description="Validated count")


# =============================================================================
# UNIFIED PARSE SCHEMAS
# =============================================================================


class ParseInput(BaseModel):
    """
    Input schema for the unified parse function.

    The parse function auto-detects the input type (name, address, or contact)
    and routes to the appropriate parser.

    Attributes:
        text: The input string to parse. Can be:
            - A name: "Dr. John Smith Jr."
            - An address: "123 Main St, Boston, MA 02101"
            - A contact (name + address): "John Smith 123 Main St, Boston, MA 02101"
        normalize: If True, normalize output to title case. Default False.
        enhance: If True, attempt to fill in missing data from database.
            This includes:
            - Looking up state from city (for addresses with city but no state)
            - Looking up city/state from street name (for addresses with street
              but no city, where the street exists in exactly one location)
            Default False.
    """

    text: str = Field(
        ...,
        description="Input string to parse (name, address, or contact)",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data from database if True",
    )


class ParseOutput(BaseModel):
    """
    Output schema for the unified parse function.

    Contains parsed name and address components, along with metadata about
    the parsing process including the detected input type and enhancement info.

    Attributes:
        name: Parsed name components (NameOutput). Empty if input was address-only.
        address: Parsed address components (AddressOutput). Empty if input was name-only.
        raw_input: The original input string, preserved for reference.
        input_type: Detected type of input: "name", "address", or "contact".
        parsed: True if parsing succeeded (extracted at least some components).
        validated: True if address city/state was validated against database.
        enhanced: True if any missing data was filled in from database.
        enhanced_fields: List of field names that were enhanced (e.g., ["city", "state"]).
        errors: List of any errors or warnings during parsing.
    """

    name: NameOutput = Field(default_factory=NameOutput, description="Parsed name")
    address: AddressOutput = Field(default_factory=AddressOutput, description="Parsed address")
    raw_input: str = Field(default="", description="Original input string")
    input_type: str = Field(default="", description="Type: name, address, or contact")
    parsed: bool = Field(default=False, description="True if parsing succeeded")
    validated: bool = Field(default=False, description="True if address validated")
    enhanced: bool = Field(default=False, description="True if data was enhanced")
    enhanced_fields: list[str] = Field(default_factory=list, description="Enhanced fields")
    errors: list[str] = Field(default_factory=list, description="Parsing errors")


class ParseBatchInput(BaseModel):
    """
    Input schema for batch parsing with the unified parse function.

    Attributes:
        texts: List of input strings to parse. Each can be a name, address,
            or contact string.
        normalize: Apply normalization to all outputs. Default False.
        enhance: Apply enhancement to all outputs. Default False.
    """

    texts: list[str] = Field(
        ...,
        description="Array of input strings to parse",
    )
    normalize: bool = Field(
        default=False,
        description="Normalize output to title case if True",
    )
    enhance: bool = Field(
        default=False,
        description="Fill in missing data from database if True",
    )


class ParseBatchOutput(BaseModel):
    """
    Output schema for batch parsing with the unified parse function.

    Contains the list of individual results plus summary statistics.

    Attributes:
        results: List of ParseOutput for each input string.
        total: Total number of strings processed.
        parsed_count: Number that were successfully parsed.
        validated_count: Number with validated addresses.
        enhanced_count: Number where data was enhanced from database.
    """

    results: list[ParseOutput] = Field(default_factory=list, description="Parsed results")
    total: int = Field(default=0, description="Total inputs processed")
    parsed_count: int = Field(default=0, description="Successfully parsed count")
    validated_count: int = Field(default=0, description="Validated count")
    enhanced_count: int = Field(default=0, description="Enhanced count")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Unified parse schemas (preferred)
    "ParseInput",
    "ParseOutput",
    "ParseBatchInput",
    "ParseBatchOutput",
    # Legacy input schemas (deprecated)
    "AddressInput",
    "NameInput",
    "ContactInput",
    "AddressBatchInput",
    "NameBatchInput",
    "ContactBatchInput",
    # Output schemas
    "AddressOutput",
    "NameOutput",
    "ContactOutput",
    "AddressBatchOutput",
    "NameBatchOutput",
    "ContactBatchOutput",
]
