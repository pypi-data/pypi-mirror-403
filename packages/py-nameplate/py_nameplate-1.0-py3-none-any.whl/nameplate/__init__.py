"""
Nameplate - US address and name parsing library.

This package provides tools for parsing unstructured US address and name
strings into structured components. It can be used as a standalone Python
library or as an MCP (Model Context Protocol) server.

Functions:
    parse: Parse any input with auto-detection (name, address, or contact)
    parse_batch: Batch parse multiple inputs

The parse() function auto-detects the input type and supports street-based
enhancement: when an address has a street name but no city/state, and that
street exists in exactly one location in the database, the city and state
are auto-filled.

Example:
    >>> from nameplate import parse
    >>>
    >>> # Parse an address (auto-detected)
    >>> result = parse("123 Main St, Boston, MA 02101")
    >>> print(result.input_type)  # "address"
    >>> print(result.address.city)  # "Boston"
    >>> print(result.validated)  # True (if in database)
    >>>
    >>> # Parse a name (auto-detected)
    >>> result = parse("Dr. John Smith Jr.")
    >>> print(result.input_type)  # "name"
    >>> print(result.name.first)  # "John"
    >>> print(result.name.prefix)  # "Dr."
    >>>
    >>> # Street-based enhancement (unique streets auto-fill city/state)
    >>> result = parse("100 Dunwoody Club Dr", enhance=True)
    >>> print(result.address.city)  # "Atlanta" (auto-filled)
    >>> print(result.enhanced_fields)  # ["city", "state"]

MCP Server:
    Run `nameplate` command to start the MCP server for Claude Code
    or other MCP-compatible clients.

    Add to ~/.claude/claude_code_config.json:
    {
        "mcpServers": {
            "nameplate": {
                "command": "nameplate"
            }
        }
    }

Schemas:
    Pydantic models for inputs and outputs are available in nameplate.schemas:
    - ParseInput, ParseOutput, ParseBatchInput, ParseBatchOutput
    - AddressOutput, NameOutput (used within ParseOutput)
"""

from nameplate.schemas import (
    AddressOutput,
    NameOutput,
    ParseBatchInput,
    ParseBatchOutput,
    ParseInput,
    ParseOutput,
)
from nameplate.tools.parse import parse, parse_batch

__version__ = "2.0.0"

__all__ = [
    "__version__",
    "parse",
    "parse_batch",
    "ParseInput",
    "ParseOutput",
    "ParseBatchInput",
    "ParseBatchOutput",
    "AddressOutput",
    "NameOutput",
]
