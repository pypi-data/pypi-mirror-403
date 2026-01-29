"""Search MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import search
from twitch_sdk.schemas.search import SearchCategoriesRequest, SearchChannelsRequest


def get_tools() -> list[Tool]:
    """Return search tools."""
    return [
        Tool(
            name="twitch_search_categories",
            description="Search for game/category names",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="twitch_search_channels",
            description="Search for channels by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "live_only": {"type": "boolean", "description": "Only show live channels"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["query"],
            },
        ),
    ]


async def _handle_search_categories(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SearchCategoriesRequest(**arguments)
    result = await search.search_categories(sdk.http, params)
    categories = [f"- {c.name} (ID: {c.id})" for c in result.data]
    return [TextContent(type="text", text=f"Categories:\n" + "\n".join(categories) if categories else "No categories found")]


async def _handle_search_channels(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SearchChannelsRequest(**arguments)
    result = await search.search_channels(sdk.http, params)
    channels = []
    for ch in result.data:
        live = " [LIVE]" if ch.is_live else ""
        channels.append(f"- {ch.display_name}{live}: {ch.title[:50]}... (ID: {ch.id})")
    return [TextContent(type="text", text=f"Channels:\n" + "\n".join(channels) if channels else "No channels found")]


def get_handlers() -> dict:
    """Return handlers for search tools."""
    return {
        "twitch_search_categories": _handle_search_categories,
        "twitch_search_channels": _handle_search_channels,
    }
