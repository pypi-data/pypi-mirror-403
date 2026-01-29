"""
MCP Server for nameplate - address and name parsing tools.

This module implements a Model Context Protocol (MCP) server that exposes
the nameplate parsing functions as tools. It can be used with Claude Code,
Claude Desktop, or any other MCP-compatible client.

Tools Provided:
    parse: Parse any input (name, address, or contact) with auto-detection
    parse_batch: Batch parse multiple inputs with auto-detection

The parse tool auto-detects the input type and routes to the appropriate
parser. It also supports street-based enhancement: when an address has a
street name but no city/state, and that street exists in exactly one
location in the database, the city and state are auto-filled.

Usage with Claude Code:
    Add to ~/.claude/claude_code_config.json:

    {
        "mcpServers": {
            "nameplate": {
                "command": "uv",
                "args": ["run", "--directory", "/path/to/py-nameplate", "nameplate"]
            }
        }
    }

    Or if installed via pip:

    {
        "mcpServers": {
            "nameplate": {
                "command": "nameplate"
            }
        }
    }

Running Directly:
    $ uv run nameplate

    Or after installation:
    $ nameplate

Testing with MCP Inspector:
    $ npx @modelcontextprotocol/inspector uv run nameplate
"""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nameplate.schemas import (
    ParseBatchInput,
    ParseInput,
)
from nameplate.tools.parse import parse, parse_batch

# =============================================================================
# SERVER SETUP
# =============================================================================

# Create the MCP server instance
# The name "nameplate" is used to identify this server to clients
server = Server("nameplate")


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Return the list of available tools.

    This is called by the MCP client to discover what tools are available.
    Each tool includes a name, description, and JSON schema for its inputs.

    Returns:
        List of Tool objects describing available parsing functions
    """
    return [
        Tool(
            name="parse",
            description=(
                "Parse any input string (name, address, or contact). "
                "Auto-detects input type and routes to appropriate parser. "
                "Supports street-based enhancement: when enhance=True and an "
                "address has a street but no city, fills in city/state if the "
                "street exists in exactly one location in the database."
            ),
            inputSchema=ParseInput.model_json_schema(),
        ),
        Tool(
            name="parse_batch",
            description=(
                "Parse an array of input strings (batch processing). "
                "Each input is auto-detected as name, address, or contact. "
                "Returns results with summary statistics including parse, "
                "validation, and enhancement counts."
            ),
            inputSchema=ParseBatchInput.model_json_schema(),
        ),
    ]


# =============================================================================
# TOOL EXECUTION
# =============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls from the MCP client.

    This is called when a client invokes one of our tools. The name
    identifies which tool to run, and arguments contains the input
    parameters.

    Args:
        name: Name of the tool to execute
        arguments: Dictionary of input arguments

    Returns:
        List containing a single TextContent with JSON-formatted result

    Raises:
        ValueError: If an unknown tool name is provided
    """
    if name == "parse":
        # Parse a single input (auto-detects type)
        result = parse(
            text=arguments.get("text", ""),
            normalize=arguments.get("normalize", False),
            enhance=arguments.get("enhance", False),
        )
        return [TextContent(type="text", text=result.model_dump_json(indent=2))]

    elif name == "parse_batch":
        # Parse multiple inputs
        result = parse_batch(
            texts=arguments.get("texts", []),
            normalize=arguments.get("normalize", False),
            enhance=arguments.get("enhance", False),
        )
        return [TextContent(type="text", text=result.model_dump_json(indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


async def _run_server():
    """
    Run the MCP server using stdio transport.

    This sets up the server to communicate with the client via
    stdin/stdout, which is the standard transport for local MCP servers.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """
    Main entry point for the nameplate MCP server.

    This function is called when running the 'nameplate' command.
    It starts the async event loop and runs the server.
    """
    asyncio.run(_run_server())


# Allow running directly with 'python -m nameplate.server'
if __name__ == "__main__":
    main()
