# =============================================================================
# Dockerfile for Nameplate MCP Server
# =============================================================================
#
# Multi-stage build for minimal image size:
#   1. Build stage: Install dependencies with uv
#   2. Runtime stage: Copy only what's needed to run
#
# The image uses Python 3.12 slim and runs as non-root user for security.
#
# =============================================================================

# -----------------------------------------------------------------------------
# Build Stage
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set up working directory
WORKDIR /app

# Copy dependency files and version file (needed for hatchling to read version)
COPY pyproject.toml uv.lock README.md ./
COPY src/nameplate/_version.py ./src/nameplate/_version.py

# Install dependencies into a virtual environment
# Using --frozen ensures we use the exact versions from uv.lock
RUN uv sync --frozen --no-dev --extra remote

# Copy remaining application code
COPY src/ ./src/

# Reinstall to pick up all source files
RUN uv sync --frozen --no-dev --extra remote

# -----------------------------------------------------------------------------
# Runtime Stage
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set up working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose port (configured via NAMEPLATE_PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the remote server
CMD ["python", "-m", "nameplate.remote_server"]
