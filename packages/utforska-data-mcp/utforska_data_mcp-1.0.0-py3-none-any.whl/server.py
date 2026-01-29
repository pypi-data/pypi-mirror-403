#!/usr/bin/env python3
"""
Data Platform MCP Server

Provides tools for AI agents to discover, fetch, and export Swedish statistical data.
Uses the MCP (Model Context Protocol) standard.
"""

import os
import json
import base64
import urllib.parse
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
BACKEND_URL = os.getenv("MCP_BACKEND_URL", "http://localhost:8000")
APP_URL = os.getenv("MCP_APP_URL", "https://utforskadata.se")
DEFAULT_LANG = os.getenv("MCP_DEFAULT_LANG", "sv")

server = Server("data-platform")


def build_search_link(
    q: str, source: str = None, category: str = None, lang: str = None
) -> str:
    """Build a link to the app search page."""
    params = {"q": q}
    if source:
        params["source"] = source
    if category:
        params["category"] = category
    if lang:
        params["lang"] = lang
    return f"{APP_URL}/search?{urllib.parse.urlencode(params)}"


def build_export_link(
    dataset_id: str,
    format: str = "csv",
    measure: str = None,
    start_year: int = None,
    end_year: int = None,
    breakdown_filters: dict = None,
    lang: str = None,
) -> str:
    """Build a link to export dataset data."""
    params = {"format": format}
    if measure:
        params["measure"] = measure
    if start_year:
        params["start_year"] = str(start_year)
    if end_year:
        params["end_year"] = str(end_year)
    if breakdown_filters:
        params["breakdown_filters"] = json.dumps(breakdown_filters)
    if lang:
        params["lang"] = lang
    return f"{BACKEND_URL}/api/v2/datasets/{dataset_id}/export?{urllib.parse.urlencode(params)}"


def build_session_link_from_intent(
    selections: list,
    title: str = None,
    description: str = None,
    lang: str = None,
) -> str:
    """Build a deep link that creates a session with preloaded data."""
    payload = {
        "version": "1",
        "lang": lang or DEFAULT_LANG,
        "selections": selections,
    }
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    # Base64url encode the payload
    payload_json = json.dumps(payload, ensure_ascii=False)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")

    return f"{APP_URL}/intent?payload={payload_b64}"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="discover_datasets",
            description="Search for datasets using AI-powered smart search. Returns datasets with reasoning about relevance. Use this to find Swedish statistical data from SCB, Skolverket, and other sources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing what data you're looking for (e.g., 'housing prices in Sweden', 'immigration statistics')",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["sv", "en"],
                        "default": "sv",
                        "description": "Response language",
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by data sources (e.g., ['scb', 'skolverket', 'worldbank'])",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by categories (e.g., ['housing', 'population', 'education'])",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of results to return",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_dataset_details",
            description="Get detailed information about a specific dataset including available measures (metrics), breakdowns (dimensions for filtering), and time range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset ID from discover_datasets results",
                    },
                    "lang": {
                        "type": "string",
                        "enum": ["sv", "en"],
                        "default": "sv",
                        "description": "Response language",
                    },
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="fetch_data",
            description="Fetch actual data from a dataset. Returns rows with values that can be used to answer questions directly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "Dataset ID"},
                    "measure": {
                        "type": "string",
                        "description": "Specific measure/metric to fetch (from dataset details)",
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "Filter data from this year",
                    },
                    "end_year": {
                        "type": "integer",
                        "description": "Filter data until this year",
                    },
                    "breakdown_filters": {
                        "type": "object",
                        "description": 'Filter by breakdown dimensions (e.g., {"region": ["SE"], "sex": ["1", "2"]})',
                    },
                    "lang": {"type": "string", "enum": ["sv", "en"], "default": "sv"},
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum rows to return",
                    },
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="build_export_link",
            description="Generate a download link for dataset data in CSV or JSON format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "Dataset ID"},
                    "format": {
                        "type": "string",
                        "enum": ["csv", "json"],
                        "default": "csv",
                    },
                    "measure": {"type": "string"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                    "breakdown_filters": {"type": "object"},
                    "lang": {"type": "string", "enum": ["sv", "en"], "default": "sv"},
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="build_search_link",
            description="Generate a link to the app's search page with the given query. Users can click this to explore datasets in the web interface.",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Search query"},
                    "source": {"type": "string"},
                    "category": {"type": "string"},
                    "lang": {"type": "string", "enum": ["sv", "en"], "default": "sv"},
                },
                "required": ["q"],
            },
        ),
        Tool(
            name="build_session_link",
            description="Generate a deep link that opens the app with preloaded data selections. Users can continue exploring, visualizing, and exporting in the web interface.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dataset_id": {"type": "string"},
                                "measures": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "time": {
                                    "type": "object",
                                    "properties": {
                                        "start_year": {"type": "integer"},
                                        "end_year": {"type": "integer"},
                                    },
                                },
                                "breakdown_filters": {"type": "object"},
                            },
                            "required": ["dataset_id"],
                        },
                        "description": "List of dataset selections to preload",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional session title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional session description",
                    },
                    "lang": {"type": "string", "enum": ["sv", "en"], "default": "sv"},
                },
                "required": ["selections"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "discover_datasets":
                # Validate query
                query = arguments.get("query", "").strip()
                if not query:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "Query parameter is required and cannot be empty",
                                    "datasets": [],
                                    "search_link": build_search_link(
                                        "", lang=arguments.get("language", DEFAULT_LANG)
                                    ),
                                },
                                indent=2,
                            ),
                        )
                    ]
                # Call AI discovery endpoint
                response = await client.post(
                    f"{BACKEND_URL}/api/ai/discover",
                    json={
                        "query": arguments["query"],
                        "language": arguments.get("language", DEFAULT_LANG),
                        "max_results": arguments.get("max_results", 5),
                        "sources": arguments.get("sources"),
                        "categories": arguments.get("categories"),
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Add search link
                data["search_link"] = build_search_link(
                    arguments["query"],
                    source=(
                        ",".join(arguments.get("sources", []))
                        if arguments.get("sources")
                        else None
                    ),
                    category=(
                        ",".join(arguments.get("categories", []))
                        if arguments.get("categories")
                        else None
                    ),
                    lang=arguments.get("language", DEFAULT_LANG),
                )

                return [
                    TextContent(
                        type="text", text=json.dumps(data, ensure_ascii=False, indent=2)
                    )
                ]

            elif name == "get_dataset_details":
                # Validate dataset_id
                dataset_id = arguments.get("dataset_id", "").strip()
                if not dataset_id:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "dataset_id parameter is required and cannot be empty"
                                },
                                indent=2,
                            ),
                        )
                    ]

                lang = arguments.get("lang", DEFAULT_LANG)
                response = await client.get(
                    f"{BACKEND_URL}/api/v2/datasets/{dataset_id}",
                    params={"lang": lang},
                )
                response.raise_for_status()
                data = response.json()

                return [
                    TextContent(
                        type="text", text=json.dumps(data, ensure_ascii=False, indent=2)
                    )
                ]

            elif name == "fetch_data":
                # Validate dataset_id
                dataset_id = arguments.get("dataset_id", "").strip()
                if not dataset_id:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "dataset_id parameter is required and cannot be empty"
                                },
                                indent=2,
                            ),
                        )
                    ]

                params = {
                    "lang": arguments.get("lang", DEFAULT_LANG),
                    "limit": arguments.get("limit", 100),
                }
                if arguments.get("measure"):
                    params["measure"] = arguments["measure"]
                if arguments.get("start_year"):
                    params["start_year"] = arguments["start_year"]
                if arguments.get("end_year"):
                    params["end_year"] = arguments["end_year"]

                response = await client.get(
                    f"{BACKEND_URL}/api/v2/datasets/{dataset_id}/data",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                # Apply breakdown filters client-side if provided
                if arguments.get("breakdown_filters") and data.get("data"):
                    filters = arguments["breakdown_filters"]
                    filtered = []
                    for row in data["data"]:
                        dims = row.get("dimensions", {})
                        match = True
                        for dim_key, allowed in filters.items():
                            if dim_key in dims and dims[dim_key] not in allowed:
                                match = False
                                break
                        if match:
                            filtered.append(row)
                    data["data"] = filtered
                    data["count"] = len(filtered)

                return [
                    TextContent(
                        type="text", text=json.dumps(data, ensure_ascii=False, indent=2)
                    )
                ]

            elif name == "build_export_link":
                # Validate dataset_id
                dataset_id = arguments.get("dataset_id", "").strip()
                if not dataset_id:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "dataset_id parameter is required and cannot be empty"
                                },
                                indent=2,
                            ),
                        )
                    ]

                link = build_export_link(
                    dataset_id=dataset_id,
                    format=arguments.get("format", "csv"),
                    measure=arguments.get("measure"),
                    start_year=arguments.get("start_year"),
                    end_year=arguments.get("end_year"),
                    breakdown_filters=arguments.get("breakdown_filters"),
                    lang=arguments.get("lang", DEFAULT_LANG),
                )
                return [
                    TextContent(
                        type="text", text=json.dumps({"export_link": link}, indent=2)
                    )
                ]

            elif name == "build_search_link":
                # Validate query
                query = arguments.get("q", "").strip()
                if not query:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "Query parameter 'q' is required and cannot be empty",
                                    "suggestion": "Provide a search query like 'housing prices' or 'immigration statistics'",
                                },
                                indent=2,
                            ),
                        )
                    ]

                link = build_search_link(
                    q=query,
                    source=arguments.get("source"),
                    category=arguments.get("category"),
                    lang=arguments.get("lang", DEFAULT_LANG),
                )
                return [
                    TextContent(
                        type="text", text=json.dumps({"search_link": link}, indent=2)
                    )
                ]

            elif name == "build_session_link":
                # Validate selections
                selections = arguments.get("selections", [])
                if not selections or len(selections) == 0:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "At least one dataset selection is required",
                                    "suggestion": "Provide selections with dataset_id and measures",
                                },
                                indent=2,
                            ),
                        )
                    ]

                # Validate each selection has required fields
                for i, sel in enumerate(selections):
                    if not sel.get("dataset_id"):
                        return [
                            TextContent(
                                type="text",
                                text=json.dumps(
                                    {
                                        "error": f"Selection {i} missing required 'dataset_id' field",
                                    },
                                    indent=2,
                                ),
                            )
                        ]
                    if not sel.get("measures") or len(sel.get("measures", [])) == 0:
                        return [
                            TextContent(
                                type="text",
                                text=json.dumps(
                                    {
                                        "error": f"Selection {i} missing required 'measures' field or it's empty",
                                    },
                                    indent=2,
                                ),
                            )
                        ]

                link = build_session_link_from_intent(
                    selections=selections,
                    title=arguments.get("title"),
                    description=arguments.get("description"),
                    lang=arguments.get("lang", DEFAULT_LANG),
                )
                return [
                    TextContent(
                        type="text", text=json.dumps({"session_link": link}, indent=2)
                    )
                ]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except httpx.HTTPStatusError as e:
            error_msg = {
                "error": f"API error: {e.response.status_code}",
                "details": (
                    e.response.text[:200] if e.response.text else "No details available"
                ),
            }

            # Add helpful messages for common errors
            if e.response.status_code == 404:
                error_msg["suggestion"] = (
                    "Dataset not found. Use discover_datasets to find valid dataset IDs."
                )
            elif e.response.status_code == 400:
                error_msg["suggestion"] = (
                    "Invalid request parameters. Check the dataset details for valid options."
                )
            elif e.response.status_code == 500:
                error_msg["suggestion"] = (
                    "Backend server error. The dataset may have data issues."
                )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(error_msg, indent=2),
                )
            ]
        except httpx.RequestError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "Connection error",
                            "details": str(e),
                            "suggestion": "Ensure the backend server is running at "
                            + BACKEND_URL,
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Unexpected error", "details": str(e)}, indent=2
                    ),
                )
            ]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
