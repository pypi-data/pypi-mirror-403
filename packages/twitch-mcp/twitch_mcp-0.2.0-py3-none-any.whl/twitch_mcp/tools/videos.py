"""Videos MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import videos
from twitch_sdk.schemas.videos import DeleteVideosRequest, GetVideosRequest


def get_tools() -> list[Tool]:
    """Return videos tools."""
    return [
        Tool(
            name="twitch_get_videos",
            description="Get videos by ID, user, or game",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Video IDs"},
                    "user_id": {"type": "string", "description": "User ID to get videos for"},
                    "game_id": {"type": "string", "description": "Game ID to get videos for"},
                    "type": {"type": "string", "description": "Filter: all, archive, highlight, upload"},
                    "sort": {"type": "string", "description": "Sort: time, trending, views"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
            },
        ),
        Tool(
            name="twitch_delete_videos",
            description="Delete videos (max 5 at once)",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Video IDs to delete (max 5)"},
                },
                "required": ["id"],
            },
        ),
    ]


async def _handle_get_videos(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetVideosRequest(**arguments)
    result = await videos.get_videos(sdk.http, params)
    video_list = []
    for v in result.data:
        video_list.append(
            f"- {v.title}\n"
            f"  By: {v.user_name} | Views: {v.view_count} | Duration: {v.duration}\n"
            f"  URL: {v.url}"
        )
    return [TextContent(type="text", text="\n".join(video_list) if video_list else "No videos found")]


async def _handle_delete_videos(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteVideosRequest(**arguments)
    deleted = await videos.delete_videos(sdk.http, params)
    return [TextContent(type="text", text=f"Deleted videos: {', '.join(deleted)}")]


def get_handlers() -> dict:
    """Return handlers for videos tools."""
    return {
        "twitch_get_videos": _handle_get_videos,
        "twitch_delete_videos": _handle_delete_videos,
    }
