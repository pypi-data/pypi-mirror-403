# Publishing to PyPI

## Prerequisites

1. Create PyPI account at https://pypi.org/account/register/
2. Create API token at https://pypi.org/manage/account/token/
3. Install build tools: `pip install build twine`

## Build the Package

```bash
cd backend/mcp-server

# Build distribution files
python -m build

# This creates:
# - dist/utforska_data_mcp-1.0.0-py3-none-any.whl
# - dist/utforska-data-mcp-1.0.0.tar.gz
```

## Test Locally

```bash
# Install locally to test
pip install -e .

# Or test with uvx
uvx --from . utforska-data-mcp
```

## Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: <your PyPI API token>
```

## Verify Installation

```bash
# Test installation from PyPI
uvx utforska-data-mcp

# Or with pip
pip install utforska-data-mcp
```

## Update Version

When releasing new versions:

1. Update version in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload: `python -m twine upload dist/*`

## Package Name

- **PyPI package:** `utforska-data-mcp`
- **Command:** `uvx utforska-data-mcp`
- **Import name:** `server`

## Configuration for Users

Users add to their MCP client config:

```json
{
  "mcpServers": {
    "utforska-data": {
      "command": "uvx",
      "args": ["utforska-data-mcp"]
    }
  }
}
```

The package installs automatically on first use via `uvx`.
