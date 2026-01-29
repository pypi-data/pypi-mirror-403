# Nameplate - Claude Code Reference

Python library, MCP server, and REST API for parsing US addresses and names. See [README.md](README.md) for full documentation.

## Coding Standards

- Use Google-style docstrings for all functions
- Add inline comments for regex patterns and non-obvious logic
- Type hints required for all function parameters and return values
- Return partial results with errors rather than raising exceptions

## Testing

```bash
uv run pytest              # Run tests
uv run pytest --cov        # With coverage
uv run ruff check src/     # Lint
uv run ruff format src/    # Format
```

## Data Management

```bash
uv run python scripts/refresh_data.py  # Download fresh source data
uv run python scripts/build_data.py    # Build SQLite database from CSV
```

## Versioning

Uses `major.minor` format (e.g., `1.0`, `1.1`, `2.0`). Version is defined in `src/nameplate/_version.py`.
