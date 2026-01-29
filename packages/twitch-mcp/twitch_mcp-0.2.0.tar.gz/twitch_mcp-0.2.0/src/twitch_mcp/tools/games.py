"""Games MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import games
from twitch_sdk.schemas.games import GetGamesRequest, GetTopGamesRequest


def get_tools() -> list[Tool]:
    """Return games tools."""
    return [
        Tool(
            name="twitch_get_games",
            description="Get game/category information by ID or name",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Game IDs"},
                    "name": {"type": "array", "items": {"type": "string"}, "description": "Game names (exact match)"},
                },
            },
        ),
        Tool(
            name="twitch_get_top_games",
            description="Get top games by current viewers",
            inputSchema={
                "type": "object",
                "properties": {
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
    ]


async def _handle_get_games(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGamesRequest(**arguments)
    result = await games.get_games(sdk.http, params)
    game_list = [f"- {g.name} (ID: {g.id})" for g in result.data]
    return [TextContent(type="text", text="\n".join(game_list) if game_list else "No games found")]


async def _handle_get_top_games(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetTopGamesRequest(**arguments) if arguments else None
    result = await games.get_top_games(sdk.http, params)
    game_list = [f"{i+1}. {g.name} (ID: {g.id})" for i, g in enumerate(result.data)]
    return [TextContent(type="text", text=f"Top Games:\n" + "\n".join(game_list))]


def get_handlers() -> dict:
    """Return handlers for games tools."""
    return {
        "twitch_get_games": _handle_get_games,
        "twitch_get_top_games": _handle_get_top_games,
    }
