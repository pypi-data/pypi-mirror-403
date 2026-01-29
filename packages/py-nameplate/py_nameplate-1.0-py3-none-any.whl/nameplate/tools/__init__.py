"""
Parsing tools for nameplate.

This subpackage contains the core parsing logic for addresses, names,
and combined contact strings.

Functions:
    parse: Parse any input (auto-detects type: name, address, or contact)
    parse_batch: Batch parse multiple inputs with auto-detection

Usage:
    >>> from nameplate.tools import parse
    >>>
    >>> # Parse an address (auto-detected)
    >>> result = parse("123 Main St, Boston, MA 02101")
    >>> print(result.input_type)  # "address"
    >>> print(result.address.city)  # "Boston"
    >>>
    >>> # Parse a name (auto-detected)
    >>> result = parse("Dr. John Smith Jr.")
    >>> print(result.input_type)  # "name"
    >>> print(result.name.first)  # "John"
    >>>
    >>> # Parse a contact (auto-detected)
    >>> result = parse("John Smith 123 Main St, Boston, MA 02101")
    >>> print(result.input_type)  # "contact"
    >>> print(result.name.last)  # "Smith"
    >>> print(result.address.city)  # "Boston"
    >>>
    >>> # Street-based enhancement (unique streets auto-fill city/state)
    >>> result = parse("100 Dunwoody Club Dr", enhance=True)
    >>> print(result.address.city)  # "Atlanta" (auto-filled)
"""

from nameplate.tools.parse import parse, parse_batch

__all__ = [
    "parse",
    "parse_batch",
]
