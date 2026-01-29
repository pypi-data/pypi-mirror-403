"""Analytics MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import analytics
from twitch_sdk.schemas.analytics import GetExtensionAnalyticsRequest, GetGameAnalyticsRequest


def get_tools() -> list[Tool]:
    """Return analytics tools."""
    return [
        Tool(
            name="twitch_get_extension_analytics",
            description="Get analytics for extensions",
            inputSchema={
                "type": "object",
                "properties": {
                    "extension_id": {"type": "string", "description": "Extension ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
        Tool(
            name="twitch_get_game_analytics",
            description="Get analytics for games",
            inputSchema={
                "type": "object",
                "properties": {
                    "game_id": {"type": "string", "description": "Game ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
    ]


async def _handle_get_extension_analytics(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetExtensionAnalyticsRequest(**arguments) if arguments else None
    result = await analytics.get_extension_analytics(sdk.http, params)
    analytics_list = [f"- Extension {a.extension_id}: {a.URL}" for a in result.data]
    return [TextContent(type="text", text="\n".join(analytics_list) if analytics_list else "No extension analytics")]


async def _handle_get_game_analytics(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGameAnalyticsRequest(**arguments) if arguments else None
    result = await analytics.get_game_analytics(sdk.http, params)
    analytics_list = [f"- Game {a.game_id}: {a.URL}" for a in result.data]
    return [TextContent(type="text", text="\n".join(analytics_list) if analytics_list else "No game analytics")]


def get_handlers() -> dict:
    """Return handlers for analytics tools."""
    return {
        "twitch_get_extension_analytics": _handle_get_extension_analytics,
        "twitch_get_game_analytics": _handle_get_game_analytics,
    }
