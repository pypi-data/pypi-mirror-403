"""Raids MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import raids
from twitch_sdk.schemas.raids import CancelRaidRequest, StartRaidRequest


def get_tools() -> list[Tool]:
    """Return raids tools."""
    return [
        Tool(
            name="twitch_start_raid",
            description="Start a raid to another channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_broadcaster_id": {"type": "string", "description": "Your broadcaster ID"},
                    "to_broadcaster_id": {"type": "string", "description": "Channel to raid"},
                },
                "required": ["from_broadcaster_id", "to_broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_cancel_raid",
            description="Cancel a pending raid",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "Your broadcaster ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_start_raid(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = StartRaidRequest(**arguments)
    result = await raids.start_raid(sdk.http, params)
    raid = result.data[0]
    return [TextContent(type="text", text=f"Raid started!\nCreated: {raid.created_at}\nMature: {raid.is_mature}")]


async def _handle_cancel_raid(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CancelRaidRequest(**arguments)
    await raids.cancel_raid(sdk.http, params)
    return [TextContent(type="text", text="Raid cancelled")]


def get_handlers() -> dict:
    """Return handlers for raids tools."""
    return {
        "twitch_start_raid": _handle_start_raid,
        "twitch_cancel_raid": _handle_cancel_raid,
    }
