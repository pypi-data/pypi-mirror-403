# py-nameplate

[![CI](https://github.com/dannyheskett/py-nameplate/actions/workflows/ci.yml/badge.svg)](https://github.com/dannyheskett/py-nameplate/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)

A Python library, MCP server, and REST API for parsing unstructured US contact strings into structured components.

## The Problem

You have messy contact data:

```
Dr. John Smith Jr. 742 Evergreen Terrace
JANE DOE 123 MAIN ST APT 2B BOSTON MA 02101
Smith, Robert "Bob" 456 Oak Ave, Chicago, IL 60601
```

You need structured data you can actually use.

## The Solution

One function that handles it all:

```python
from nameplate import parse

result = parse("Dr. John Smith Jr. 742 Evergreen Terrace, Springfield, IL 62701")

# Name components
result.name.prefix      # "Dr."
result.name.first       # "John"
result.name.last        # "Smith"
result.name.suffix      # "Jr."

# Address components
result.address.street_number  # "742"
result.address.street_name    # "Evergreen"
result.address.street_type    # "Terrace"
result.address.city           # "Springfield"
result.address.state          # "IL"

result.input_type       # "contact"
result.validated        # True (city/state in database)
```

## How It Works

The `parse()` function uses token-based segmentation to automatically find the boundary between name and address:

```
Dr. John Smith Jr. 742 Evergreen Terrace
└───── name ─────┘ └────── address ─────┘
```

**Segmentation algorithm:**
1. Tokenize input into words
2. Scan for first numeric token that isn't a name suffix (III, 1ST, etc.)
3. Verify remaining tokens contain street indicators (St, Ave, ZIP, state, etc.)
4. Split at that boundary

**Address parsing** works backwards from the end:
- Extract ZIP code (5 or 9 digits)
- Extract state (2-letter code)
- Extract city (validated against database)
- Extract unit (Apt, Suite, #)
- Remaining tokens are street components

**Street-based enhancement** fills in missing city/state:
- If address has a street but no city, look up the street in the database
- If street exists in exactly one location, auto-fill city and state
- Common streets like "Main Street" exist in many cities and won't enhance

## Installation

```bash
pip install py-nameplate
```

Or with uv:

```bash
uv add py-nameplate
```

## Usage

### Basic Parsing

```python
from nameplate import parse

# Auto-detects input type
result = parse("123 Main St, Boston, MA 02101")
result.input_type  # "address"

result = parse("Dr. Jane Doe")
result.input_type  # "name"

result = parse("John Smith 123 Main St, Boston, MA 02101")
result.input_type  # "contact"
```

### Enhancement

```python
# Without enhancement - street alone has no city/state
result = parse("100 Dunwoody Club Dr")
result.address.city   # ""
result.address.state  # ""

# With enhancement - city/state auto-filled if street is unique in database
result = parse("100 Dunwoody Club Dr", enhance=True)
result.address.city   # "Atlanta" (auto-filled)
result.address.state  # "GA" (auto-filled)
result.enhanced       # True
```

### Normalization

```python
# Smart title case
result = parse("PATRICK O'BRIEN 123 MAIN ST", normalize=True)
result.name.last       # "O'Brien" (not "O'brien")
result.address.city    # "Boston" (not "BOSTON")

result = parse("RONALD MCDONALD", normalize=True)
result.name.last  # "McDonald" (not "Mcdonald")
```

### Batch Processing

```python
from nameplate import parse_batch

texts = [
    "Dr. John Smith",
    "123 Main St, Boston, MA 02101",
    "Jane Doe 456 Oak Ave, Chicago, IL 60601",
]
result = parse_batch(texts, enhance=True)
result.total           # 3
result.parsed_count    # 3
result.enhanced_count  # number with enhanced data
```

## Supported Formats

### Names

| Format | Example |
|--------|---------|
| Simple | `John Smith` |
| With prefix | `Dr. Jane Doe`, `Lt. Col. John Smith` |
| With suffix | `John Smith Jr.`, `Jane Doe PhD` |
| Last, First | `Smith, John` |
| With nickname | `Robert "Bob" Smith` |
| Name particles | `Ludwig van Beethoven`, `Juan de la Vega` |
| Roman numerals | `Henry Ford III` |

### Addresses

| Format | Example |
|--------|---------|
| Standard | `123 Main St, Boston, MA 02101` |
| With unit | `456 Oak Ave Apt 2B, Chicago, IL 60601` |
| PO Box | `PO Box 789, Miami, FL 33101` |
| Directional | `100 N Main St, Denver, CO 80202` |
| ZIP+4 | `123 Main St, Boston, MA 02101-1234` |

### Contacts

Any combination of name followed by address:

```
John Smith 123 Main St, Boston, MA 02101
Dr. Jane Doe Jr. PO Box 456, Seattle, WA 98101
```

## MCP Server

Use with Claude Desktop or Claude.ai as an MCP tool.

### Local (uvx)

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nameplate": {
      "command": "uvx",
      "args": ["nameplate"]
    }
  }
}
```

### Hosted

```json
{
  "mcpServers": {
    "nameplate": {
      "type": "url",
      "url": "https://nameplate.mcp.danheskett.com/"
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `parse` | Parse any input with auto-detection and optional enhancement |
| `parse_batch` | Batch parse multiple inputs |

### Example Prompts

> "Parse this: Dr. John Smith 742 Evergreen Terrace, Springfield, IL"

> "Parse with enhancement: Jane Doe 100 Dunwoody Club Dr"

> "Parse these contacts: John Smith, 123 Main St Boston MA, Jane Doe 456 Oak Ave Chicago IL"

## REST API

Use the REST API for direct HTTP access without MCP.

**Base URL:** `https://nameplate.mcp.danheskett.com`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/parse` | POST | Parse a single input |
| `/api/parse/batch` | POST | Parse multiple inputs |
| `/health` | GET | Health check |

### Request Format

```json
{
  "text": "Dr. John Smith 123 Main St, Boston, MA 02101",
  "normalize": false,
  "enhance": false
}
```

For batch requests, use `texts` (array) instead of `text`:

```json
{
  "texts": ["John Smith", "123 Main St, Boston, MA 02101"],
  "normalize": true,
  "enhance": true
}
```

### Examples

**Basic parse:**

```bash
curl -X POST https://nameplate.mcp.danheskett.com/api/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Dr. John Smith 123 Main St, Boston, MA 02101"}'
```

**Parse with enhancement:**

```bash
curl -X POST https://nameplate.mcp.danheskett.com/api/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Jane Doe 100 Dunwoody Club Dr", "enhance": true}'
```

**Batch parsing:**

```bash
curl -X POST https://nameplate.mcp.danheskett.com/api/parse/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["John Smith", "123 Main St, Boston, MA 02101"], "normalize": true}'
```

**Health check:**

```bash
curl https://nameplate.mcp.danheskett.com/health
```

## Python API Reference

### parse(text, normalize=False, enhance=False) -> ParseOutput

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | str | Input string to parse |
| `normalize` | bool | Apply smart title case |
| `enhance` | bool | Fill in missing data from database |

### ParseOutput

| Field | Type | Description |
|-------|------|-------------|
| `input_type` | str | "name", "address", or "contact" |
| `name` | NameOutput | Parsed name components |
| `address` | AddressOutput | Parsed address components |
| `parsed` | bool | True if parsing succeeded |
| `validated` | bool | True if city/state found in database |
| `enhanced` | bool | True if data was enhanced |
| `enhanced_fields` | list[str] | Fields that were enhanced |
| `errors` | list[str] | Any parsing errors |

### NameOutput

| Field | Type | Description |
|-------|------|-------------|
| `prefix` | str | Dr., Mr., Mrs., Rev., etc. |
| `first` | str | First/given name |
| `middle` | str | Middle name(s) |
| `last` | str | Last/family name |
| `suffix` | str | Jr., Sr., III, PhD, etc. |
| `nickname` | str | Nickname if present |

### AddressOutput

| Field | Type | Description |
|-------|------|-------------|
| `street_number` | str | House/building number |
| `street_name` | str | Street name |
| `street_type` | str | St, Ave, Blvd, etc. |
| `street_direction` | str | N, S, E, W, etc. |
| `unit_type` | str | Apt, Suite, Unit, etc. |
| `unit_number` | str | Unit/apartment number |
| `city` | str | City name |
| `state` | str | Two-letter state code |
| `zip_code` | str | 5 or 9 digit ZIP |

## Data Sources

- **US Cities**: 29,880 city/state combinations from [kelvins/US-Cities-Database](https://github.com/kelvins/US-Cities-Database) (MIT)
- **Street Names**: 500k+ street/location mappings from [USGS](https://geonames.usgs.gov/domestic/stnames.htm) (ODbL)

## Development

```bash
git clone https://github.com/dannyheskett/py-nameplate.git
cd py-nameplate
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Privacy

The hosted MCP server does not store, log, or retain any data. All parsing happens in memory. See the [source code](src/nameplate/remote_server.py) to verify.

## License

BSD-3-Clause
