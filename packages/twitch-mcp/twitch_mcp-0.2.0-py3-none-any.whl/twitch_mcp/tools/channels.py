"""Channels MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import channels
from twitch_sdk.schemas.channels import (
    AddVIPRequest,
    GetChannelEditorsRequest,
    GetChannelFollowersRequest,
    GetChannelInfoRequest,
    GetFollowedChannelsRequest,
    GetVIPsRequest,
    ModifyChannelInfoRequest,
    RemoveVIPRequest,
)


def get_tools() -> list[Tool]:
    """Return channels tools."""
    return [
        Tool(
            name="twitch_get_channel_info",
            description="Get information about one or more channels",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "array", "items": {"type": "string"}, "description": "Broadcaster IDs"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_modify_channel_info",
            description="Modify channel information (title, game, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "game_id": {"type": "string", "description": "The game/category ID"},
                    "title": {"type": "string", "description": "The stream title"},
                    "broadcaster_language": {"type": "string", "description": "Language code (e.g., 'en')"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Stream tags"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_get_channel_followers",
            description="Get list of users that follow a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_get_followed_channels",
            description="Get channels that a user follows",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The user ID"},
                    "broadcaster_id": {"type": "string", "description": "Check if following specific broadcaster"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="twitch_get_vips",
            description="Get list of VIPs for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_add_vip",
            description="Add a VIP to the channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "string", "description": "The user ID to make VIP"},
                },
                "required": ["broadcaster_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_remove_vip",
            description="Remove a VIP from the channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "string", "description": "The user ID to remove as VIP"},
                },
                "required": ["broadcaster_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_get_channel_editors",
            description="Get list of channel editors",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_get_channel_info(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChannelInfoRequest(**arguments)
    result = await channels.get_channel_information(sdk.http, params)
    info = []
    for ch in result.data:
        info.append(
            f"- {ch.broadcaster_name}\n"
            f"  Title: {ch.title}\n"
            f"  Game: {ch.game_name}\n"
            f"  Language: {ch.broadcaster_language}\n"
            f"  Tags: {', '.join(ch.tags)}"
        )
    return [TextContent(type="text", text="\n".join(info) if info else "No channels found")]


async def _handle_modify_channel_info(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = ModifyChannelInfoRequest(**arguments)
    await channels.modify_channel_information(sdk.http, params)
    return [TextContent(type="text", text="Channel information updated successfully")]


async def _handle_get_channel_followers(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChannelFollowersRequest(**arguments)
    result = await channels.get_channel_followers(sdk.http, params)
    followers = [f"- {f.user_name} (since {f.followed_at.date()})" for f in result.data]
    return [TextContent(type="text", text=f"Followers ({result.total}):\n" + "\n".join(followers[:50]))]


async def _handle_get_followed_channels(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetFollowedChannelsRequest(**arguments)
    result = await channels.get_followed_channels(sdk.http, params)
    followed = [f"- {f.broadcaster_name}" for f in result.data]
    return [TextContent(type="text", text=f"Following:\n" + "\n".join(followed))]


async def _handle_get_vips(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetVIPsRequest(**arguments)
    result = await channels.get_vips(sdk.http, params)
    vips = [f"- {v.user_name}" for v in result.data]
    return [TextContent(type="text", text=f"VIPs:\n" + "\n".join(vips) if vips else "No VIPs")]


async def _handle_add_vip(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = AddVIPRequest(**arguments)
    await channels.add_channel_vip(sdk.http, params)
    return [TextContent(type="text", text="VIP added successfully")]


async def _handle_remove_vip(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = RemoveVIPRequest(**arguments)
    await channels.remove_channel_vip(sdk.http, params)
    return [TextContent(type="text", text="VIP removed successfully")]


async def _handle_get_channel_editors(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChannelEditorsRequest(**arguments)
    result = await channels.get_channel_editors(sdk.http, params)
    editors = [f"- {e.user_name} (since {e.created_at.date()})" for e in result.data]
    return [TextContent(type="text", text=f"Channel Editors:\n" + "\n".join(editors) if editors else "No editors")]


def get_handlers() -> dict:
    """Return handlers for channels tools."""
    return {
        "twitch_get_channel_info": _handle_get_channel_info,
        "twitch_modify_channel_info": _handle_modify_channel_info,
        "twitch_get_channel_followers": _handle_get_channel_followers,
        "twitch_get_followed_channels": _handle_get_followed_channels,
        "twitch_get_vips": _handle_get_vips,
        "twitch_add_vip": _handle_add_vip,
        "twitch_remove_vip": _handle_remove_vip,
        "twitch_get_channel_editors": _handle_get_channel_editors,
    }
