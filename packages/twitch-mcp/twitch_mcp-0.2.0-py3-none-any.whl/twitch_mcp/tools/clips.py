"""Clips MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import clips
from twitch_sdk.schemas.clips import CreateClipRequest, GetClipsRequest


def get_tools() -> list[Tool]:
    """Return clips tools."""
    return [
        Tool(
            name="twitch_create_clip",
            description="Create a clip from a live stream",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "has_delay": {"type": "boolean", "description": "Add delay for clip processing"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_get_clips",
            description="Get clips for a broadcaster or game",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "game_id": {"type": "string", "description": "The game ID"},
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Specific clip IDs"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
    ]


async def _handle_create_clip(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateClipRequest(**arguments)
    result = await clips.create_clip(sdk.http, params)
    clip = result.data[0]
    return [TextContent(type="text", text=f"Clip created!\nID: {clip.id}\nEdit URL: {clip.edit_url}")]


async def _handle_get_clips(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetClipsRequest(**arguments)
    result = await clips.get_clips(sdk.http, params)
    clip_list = []
    for c in result.data:
        clip_list.append(
            f"- {c.title}\n"
            f"  By: {c.creator_name} | Views: {c.view_count}\n"
            f"  URL: {c.url}"
        )
    return [TextContent(type="text", text="\n".join(clip_list) if clip_list else "No clips found")]


def get_handlers() -> dict:
    """Return handlers for clips tools."""
    return {
        "twitch_create_clip": _handle_create_clip,
        "twitch_get_clips": _handle_get_clips,
    }
