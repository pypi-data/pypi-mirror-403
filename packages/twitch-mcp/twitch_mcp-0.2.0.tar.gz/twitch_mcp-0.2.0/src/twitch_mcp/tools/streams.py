"""Streams MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import streams
from twitch_sdk.schemas.streams import (
    CreateStreamMarkerRequest,
    GetFollowedStreamsRequest,
    GetStreamsRequest,
)


def get_tools() -> list[Tool]:
    """Return streams tools."""
    return [
        Tool(
            name="twitch_get_streams",
            description="Get active live streams, optionally filtered by user/game",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "array", "items": {"type": "string"}, "description": "Filter by user IDs"},
                    "user_login": {"type": "array", "items": {"type": "string"}, "description": "Filter by user logins"},
                    "game_id": {"type": "array", "items": {"type": "string"}, "description": "Filter by game IDs"},
                    "language": {"type": "array", "items": {"type": "string"}, "description": "Filter by language"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
        Tool(
            name="twitch_get_followed_streams",
            description="Get streams from channels that a user follows",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The user ID to get followed streams for"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="twitch_create_stream_marker",
            description="Create a marker in a live stream",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "description": {"type": "string", "description": "Description for the marker (max 140 chars)"},
                },
                "required": ["user_id"],
            },
        ),
    ]


async def _handle_get_streams(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetStreamsRequest(**arguments) if arguments else None
    result = await streams.get_streams(sdk.http, params)
    stream_list = []
    for s in result.data:
        stream_list.append(
            f"- {s.user_name}: {s.title}\n"
            f"  Game: {s.game_name} | Viewers: {s.viewer_count} | Started: {s.started_at}"
        )
    return [TextContent(type="text", text=f"Live Streams:\n" + "\n".join(stream_list) if stream_list else "No streams found")]


async def _handle_get_followed_streams(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetFollowedStreamsRequest(**arguments)
    result = await streams.get_followed_streams(sdk.http, params)
    stream_list = []
    for s in result.data:
        stream_list.append(f"- {s.user_name}: {s.title} ({s.viewer_count} viewers)")
    return [TextContent(type="text", text=f"Followed Streams:\n" + "\n".join(stream_list) if stream_list else "No followed streams live")]


async def _handle_create_stream_marker(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateStreamMarkerRequest(**arguments)
    result = await streams.create_stream_marker(sdk.http, params)
    marker = result.data[0]
    return [TextContent(type="text", text=f"Marker created at position {marker.position_seconds}s: {marker.description}")]


def get_handlers() -> dict:
    """Return handlers for streams tools."""
    return {
        "twitch_get_streams": _handle_get_streams,
        "twitch_get_followed_streams": _handle_get_followed_streams,
        "twitch_create_stream_marker": _handle_create_stream_marker,
    }
