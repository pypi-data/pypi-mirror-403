"""Ads MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import ads
from twitch_sdk.schemas.ads import GetAdScheduleRequest, SnoozeNextAdRequest, StartCommercialRequest


def get_tools() -> list[Tool]:
    """Return ads tools."""
    return [
        Tool(
            name="twitch_start_commercial",
            description="Start a commercial break on a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "length": {"type": "integer", "description": "Commercial length: 30, 60, 90, 120, 150, or 180 seconds"},
                },
                "required": ["broadcaster_id", "length"],
            },
        ),
        Tool(
            name="twitch_get_ad_schedule",
            description="Get ad schedule for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_snooze_next_ad",
            description="Snooze the next scheduled ad break",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_start_commercial(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = StartCommercialRequest(**arguments)
    result = await ads.start_commercial(sdk.http, params)
    ad = result.data[0]
    return [TextContent(type="text", text=f"Commercial started: {ad.length}s\nRetry after: {ad.retry_after}s")]


async def _handle_get_ad_schedule(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetAdScheduleRequest(**arguments)
    result = await ads.get_ad_schedule(sdk.http, params)
    schedule = result.data[0]
    return [TextContent(type="text", text=f"Ad Schedule:\n"
        f"Next ad: {schedule.next_ad_at}\n"
        f"Last ad: {schedule.last_ad_at}\n"
        f"Snooze count: {schedule.snooze_count}")]


async def _handle_snooze_next_ad(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SnoozeNextAdRequest(**arguments)
    result = await ads.snooze_next_ad(sdk.http, params)
    snooze = result.data[0]
    return [TextContent(type="text", text=f"Ad snoozed!\nNext ad: {snooze.next_ad_at}\nSnoozes remaining: {snooze.snooze_count}")]


def get_handlers() -> dict:
    """Return handlers for ads tools."""
    return {
        "twitch_start_commercial": _handle_start_commercial,
        "twitch_get_ad_schedule": _handle_get_ad_schedule,
        "twitch_snooze_next_ad": _handle_snooze_next_ad,
    }
