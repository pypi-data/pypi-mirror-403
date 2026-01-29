# Data Platform MCP Server

MCP (Model Context Protocol) server for AI agents to discover, fetch, and export Swedish statistical data.

## Tools

- **discover_datasets** - AI-powered smart search for datasets
- **get_dataset_details** - Get measures, breakdowns, and time ranges
- **fetch_data** - Fetch actual data rows for direct answers
- **build_export_link** - Generate CSV/JSON download links
- **build_search_link** - Link to app search page
- **build_session_link** - Deep link to preload data in the app

## Installation

The package is available on PyPI and installs automatically via `uvx`:

```bash
# No manual installation needed - uvx handles it automatically
# Just add to your MCP client config (see below)
```

For development:

```bash
cd backend/mcp-server
pip install -e .
```

## Usage with MCP Clients

Add to your MCP client config:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

**Windsurf** (`~/.codeium/windsurf/mcp_config.json`):

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

**Cursor/Cline**: Same configuration format.

The package installs automatically on first use. No manual installation required!

## Configuration

The server connects to the production backend by default. No environment variables needed for normal use.

For development:

- `MCP_BACKEND_URL` - Backend API URL (default: `https://data-platform-production.up.railway.app`)
- `MCP_APP_URL` - Frontend app URL (default: `https://utforskadata.se`)
- `MCP_DEFAULT_LANG` - Default language (default: `sv`)

## Example Flows

### Quick Answer

1. `discover_datasets("housing prices in Sweden")`
2. `get_dataset_details(dataset_id)` - check measures/breakdowns
3. `fetch_data(dataset_id, measure="Average price")` - get data
4. Answer the question with the data
5. Offer `build_export_link()` and `build_search_link()`

### Deep Dive

1. Same as above
2. `build_session_link(selections=[...])` - create link to continue in app
