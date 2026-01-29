"""
Remote MCP Server for nameplate - Streamable HTTP transport.

This module implements a remote-capable MCP server using the Streamable HTTP
transport (MCP spec 2025-06-18). It can be deployed to cloud platforms to
provide nameplate parsing as a remote service.

The server exposes the unified parse() function which auto-detects input type
(name, address, or contact) and supports street-based enhancement.

Usage:
    # Development
    uv run uvicorn nameplate.remote_server:app --reload --port 8000

    # Production (via entry point)
    nameplate-remote

    # With custom host/port
    nameplate-remote --host 0.0.0.0 --port 8080

Environment Variables:
    NAMEPLATE_HOST: Host to bind to (default: 0.0.0.0)
    NAMEPLATE_PORT: Port to bind to (default: 8000)
    NAMEPLATE_RATE_LIMIT: Requests per minute (default: 60)

Endpoints:
    GET/POST /       - MCP Streamable HTTP endpoint
    GET      /health - Health check
    POST     /api/*  - Direct API endpoints (non-MCP)
"""

import argparse
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from time import time

from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from nameplate.schemas import (
    ParseBatchInput,
    ParseInput,
)
from nameplate.tools.parse import parse, parse_batch

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default configuration from environment
DEFAULT_HOST = os.environ.get("NAMEPLATE_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.environ.get("NAMEPLATE_PORT", "8000"))
RATE_LIMIT = int(os.environ.get("NAMEPLATE_RATE_LIMIT", "60"))

# =============================================================================
# MCP SERVER SETUP
# =============================================================================

# Create the MCP server instance
mcp_server = Server("nameplate")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Return the list of available tools."""
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


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    if name == "parse":
        result = parse(
            text=arguments.get("text", ""),
            normalize=arguments.get("normalize", False),
            enhance=arguments.get("enhance", False),
        )
        return [TextContent(type="text", text=result.model_dump_json(indent=2))]

    elif name == "parse_batch":
        result = parse_batch(
            texts=arguments.get("texts", []),
            normalize=arguments.get("normalize", False),
            enhance=arguments.get("enhance", False),
        )
        return [TextContent(type="text", text=result.model_dump_json(indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# =============================================================================
# RATE LIMITING MIDDLEWARE
# =============================================================================

# Simple in-memory rate limiting
# For production, use Redis or similar
request_counts: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client is within rate limit.

    Args:
        client_ip: The client's IP address.

    Returns:
        True if within rate limit, False if exceeded.
    """
    now = time()
    minute_ago = now - 60

    # Clean old requests
    request_counts[client_ip] = [t for t in request_counts[client_ip] if t > minute_ago]

    # Check limit
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return False

    # Record request
    request_counts[client_ip].append(now)
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on all requests."""

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        # Get client IP, handling proxies
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Please try again later."},
            )

        return await call_next(request)


# =============================================================================
# HTTP ENDPOINTS
# =============================================================================


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for load balancers."""
    return JSONResponse({"status": "healthy", "service": "nameplate"})


async def root(request: Request) -> JSONResponse:
    """Root endpoint with service info."""
    return JSONResponse(
        {
            "service": "nameplate",
            "version": "2.0.0",
            "description": "MCP server for US address and name parsing",
            "transport": "Streamable HTTP (MCP spec 2025-06-18)",
            "endpoints": {
                "mcp": "/mcp",
                "health": "/health",
                "api": {
                    "parse": "/api/parse",
                    "parse_batch": "/api/parse/batch",
                },
            },
        }
    )


# =============================================================================
# DIRECT API ENDPOINTS (non-MCP)
# =============================================================================


async def api_parse(request: Request) -> JSONResponse:
    """
    Direct API endpoint for unified parsing.

    Accepts POST with JSON body:
        - text: Input string to parse
        - normalize: Optional, normalize to title case (default: false)
        - enhance: Optional, fill in missing data (default: false)

    Returns parsed result with auto-detected input type.
    """
    body = await request.json()
    result = parse(
        text=body.get("text", ""),
        normalize=body.get("normalize", False),
        enhance=body.get("enhance", False),
    )
    return JSONResponse(content=result.model_dump())


async def api_parse_batch(request: Request) -> JSONResponse:
    """
    Direct API endpoint for batch parsing.

    Accepts POST with JSON body:
        - texts: Array of input strings to parse
        - normalize: Optional, normalize to title case (default: false)
        - enhance: Optional, fill in missing data (default: false)

    Returns batch results with summary statistics.
    """
    body = await request.json()
    result = parse_batch(
        texts=body.get("texts", []),
        normalize=body.get("normalize", False),
        enhance=body.get("enhance", False),
    )
    return JSONResponse(content=result.model_dump())


# =============================================================================
# STARLETTE APPLICATION
# =============================================================================

# Create session manager for MCP Streamable HTTP transport
# - stateless=True: Each request is independent (tools are pure functions)
# - json_response=True: Return JSON instead of SSE for tool calls
session_manager = StreamableHTTPSessionManager(
    app=mcp_server,
    json_response=True,
    stateless=True,
)


@asynccontextmanager
async def lifespan(app: Starlette):
    """
    Application lifespan handler.

    Manages the StreamableHTTPSessionManager lifecycle. The session manager
    must be started before handling requests and properly shut down after.
    """
    print(f"Nameplate remote server starting on port {DEFAULT_PORT}")
    async with session_manager.run():
        yield
    print("Nameplate remote server shutting down")


# Define middleware stack
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    Middleware(RateLimitMiddleware),
]

# Define routes
# Note: MCP endpoint is mounted at root, other routes take precedence
routes = [
    # Health and info endpoints (these take precedence over the mount)
    Route("/health", health_check, methods=["GET"]),
    # Direct API endpoints for non-MCP access
    Route("/api/parse", api_parse, methods=["POST"]),
    Route("/api/parse/batch", api_parse_batch, methods=["POST"]),
    # MCP Streamable HTTP endpoint - Mount at root (handles GET, POST, DELETE)
    Mount("/", app=session_manager.handle_request),
]

# Create the Starlette application
app = Starlette(
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    """Main entry point for the remote server."""
    parser = argparse.ArgumentParser(
        description="Nameplate remote MCP server",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind to (default: {DEFAULT_PORT})",
    )

    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "nameplate.remote_server:app",
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
