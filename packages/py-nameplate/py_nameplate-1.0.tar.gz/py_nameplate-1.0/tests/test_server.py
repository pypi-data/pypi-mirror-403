"""
Tests for MCP server functionality.

This module tests the MCP server implementation, including
tool registration, tool execution, and error handling.

Test Categories:
    - Server setup: Server instance creation
    - Tool listing: list_tools() returns correct tools
    - Tool execution: call_tool() processes requests correctly
    - Error handling: Unknown tools, invalid inputs
    - JSON output: Results are valid JSON
"""

import asyncio
import json

import pytest

from nameplate.server import call_tool, list_tools, server

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def run_async(coro):
    """Run an async function synchronously for testing."""
    return asyncio.new_event_loop().run_until_complete(coro)


# =============================================================================
# SERVER SETUP TESTS
# =============================================================================


class TestServerSetup:
    """Tests for MCP server setup."""

    def test_server_exists(self):
        """Server instance should exist."""
        assert server is not None

    def test_server_name(self):
        """Server should be named 'nameplate'."""
        assert server.name == "nameplate"


# =============================================================================
# TOOL LISTING TESTS
# =============================================================================


class TestToolListing:
    """Tests for tool listing functionality."""

    def test_list_tools_returns_list(self):
        """list_tools should return a list."""
        tools = run_async(list_tools())
        assert isinstance(tools, list)

    def test_list_tools_count(self):
        """Should have 2 tools registered (parse and parse_batch)."""
        tools = run_async(list_tools())
        assert len(tools) == 2

    def test_list_tools_names(self):
        """All expected tools should be registered."""
        tools = run_async(list_tools())
        tool_names = [t.name for t in tools]

        assert "parse" in tool_names
        assert "parse_batch" in tool_names

    def test_tools_have_descriptions(self):
        """Each tool should have a description."""
        tools = run_async(list_tools())

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    def test_tools_have_input_schema(self):
        """Each tool should have an input schema."""
        tools = run_async(list_tools())

        for tool in tools:
            assert tool.inputSchema is not None
            assert isinstance(tool.inputSchema, dict)


# =============================================================================
# PARSE TOOL TESTS
# =============================================================================


class TestParseTool:
    """Tests for the unified parse tool."""

    def test_parse_address(self):
        """parse tool should parse an address."""
        result = run_async(call_tool("parse", {"text": "123 Main St, Boston, MA 02101"}))

        assert len(result) == 1
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["input_type"] == "address"
        assert data["address"]["city"] == "Boston"
        assert data["address"]["state"] == "MA"
        assert data["parsed"] is True

    def test_parse_name(self):
        """parse tool should parse a name."""
        result = run_async(call_tool("parse", {"text": "Dr. John Smith Jr."}))

        data = json.loads(result[0].text)
        assert data["input_type"] == "name"
        assert data["name"]["prefix"] == "Dr."
        assert data["name"]["first"] == "John"
        assert data["name"]["last"] == "Smith"
        assert data["parsed"] is True

    def test_parse_contact(self):
        """parse tool should parse a contact."""
        result = run_async(call_tool("parse", {"text": "John Smith 123 Main St, Boston, MA 02101"}))

        data = json.loads(result[0].text)
        assert data["input_type"] == "contact"
        assert data["name"]["first"] == "John"
        assert data["address"]["city"] == "Boston"
        assert data["parsed"] is True

    def test_parse_with_normalize(self):
        """parse tool with normalize flag."""
        result = run_async(
            call_tool(
                "parse",
                {"text": "123 MAIN ST, BOSTON, MA 02101", "normalize": True},
            )
        )

        data = json.loads(result[0].text)
        assert data["address"]["city"] == "Boston"  # Should be normalized

    def test_parse_with_enhance(self):
        """parse tool with enhance flag."""
        result = run_async(
            call_tool(
                "parse",
                {"text": "123 Main St, Boston, MA 02101", "enhance": True},
            )
        )

        data = json.loads(result[0].text)
        assert data["parsed"] is True


# =============================================================================
# BATCH PARSE TOOL TESTS
# =============================================================================


class TestParseBatchTool:
    """Tests for the batch parse tool."""

    def test_parse_batch_multiple_inputs(self):
        """parse_batch tool should parse multiple inputs."""
        result = run_async(
            call_tool(
                "parse_batch",
                {
                    "texts": [
                        "John Smith",
                        "123 Main St, Boston, MA 02101",
                        "Jane Doe 456 Oak Ave, Chicago, IL 60601",
                    ]
                },
            )
        )

        data = json.loads(result[0].text)
        assert data["total"] == 3
        assert data["parsed_count"] == 3
        assert len(data["results"]) == 3

        # Verify auto-detection
        assert data["results"][0]["input_type"] == "name"
        assert data["results"][1]["input_type"] == "address"
        assert data["results"][2]["input_type"] == "contact"

    def test_parse_batch_with_normalize(self):
        """parse_batch with normalize flag."""
        result = run_async(
            call_tool(
                "parse_batch",
                {"texts": ["JOHN SMITH", "123 MAIN ST, BOSTON, MA 02101"], "normalize": True},
            )
        )

        data = json.loads(result[0].text)
        assert data["results"][0]["name"]["first"] == "John"
        assert data["results"][1]["address"]["city"] == "Boston"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in tool execution."""

    def test_unknown_tool_raises(self):
        """Unknown tool name should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            run_async(call_tool("unknown_tool", {}))

        assert "Unknown tool" in str(exc_info.value)

    def test_empty_text_handled(self):
        """Empty text should be handled gracefully."""
        result = run_async(call_tool("parse", {"text": ""}))

        data = json.loads(result[0].text)
        assert data["parsed"] is False
        assert len(data["errors"]) > 0

    def test_missing_required_field_uses_default(self):
        """Missing required field should use empty default."""
        result = run_async(call_tool("parse", {}))

        data = json.loads(result[0].text)
        assert data["parsed"] is False

    def test_empty_batch_handled(self):
        """Empty batch should be handled gracefully."""
        result = run_async(call_tool("parse_batch", {"texts": []}))

        data = json.loads(result[0].text)
        assert data["total"] == 0
        assert data["parsed_count"] == 0


# =============================================================================
# JSON OUTPUT TESTS
# =============================================================================


class TestJsonOutput:
    """Tests for JSON output formatting."""

    def test_output_is_valid_json(self):
        """Tool output should be valid JSON."""
        result = run_async(call_tool("parse", {"text": "123 Main St, Boston, MA 02101"}))

        # Should not raise
        data = json.loads(result[0].text)
        assert isinstance(data, dict)

    def test_output_is_indented(self):
        """Tool output should be indented for readability."""
        result = run_async(call_tool("parse", {"text": "123 Main St, Boston, MA 02101"}))

        # Check that the JSON is indented (has newlines)
        assert "\n" in result[0].text

    def test_batch_output_structure(self):
        """Batch output should have correct structure."""
        result = run_async(
            call_tool(
                "parse_batch",
                {"texts": ["123 Main St, Boston, MA 02101"]},
            )
        )

        data = json.loads(result[0].text)

        assert "results" in data
        assert "total" in data
        assert "parsed_count" in data
        assert "enhanced_count" in data
        assert isinstance(data["results"], list)


# =============================================================================
# TOOL SCHEMA TESTS
# =============================================================================


class TestToolSchemas:
    """Tests for tool input schemas."""

    def test_parse_tool_schema(self):
        """parse schema should have expected fields."""
        tools = run_async(list_tools())
        parse_tool = next(t for t in tools if t.name == "parse")

        schema = parse_tool.inputSchema
        assert "properties" in schema
        assert "text" in schema["properties"]
        assert "normalize" in schema["properties"]
        assert "enhance" in schema["properties"]

    def test_parse_batch_tool_schema(self):
        """parse_batch schema should have expected fields."""
        tools = run_async(list_tools())
        batch_tool = next(t for t in tools if t.name == "parse_batch")

        schema = batch_tool.inputSchema
        assert "properties" in schema
        assert "texts" in schema["properties"]
        assert "normalize" in schema["properties"]
        assert "enhance" in schema["properties"]
