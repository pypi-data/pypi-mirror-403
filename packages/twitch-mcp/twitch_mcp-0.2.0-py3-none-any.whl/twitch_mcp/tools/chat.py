"""Chat MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import chat
from twitch_sdk.schemas.chat import (
    GetChattersRequest,
    GetChatSettingsRequest,
    GetEmotesRequest,
    SendAnnouncementRequest,
    SendMessageRequest,
    ShoutoutRequest,
    UpdateChatSettingsRequest,
)


def get_tools() -> list[Tool]:
    """Return chat tools."""
    return [
        Tool(
            name="twitch_send_chat_message",
            description="Send a message to a broadcaster's chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "sender_id": {"type": "string", "description": "The sender's user ID"},
                    "message": {"type": "string", "description": "The message to send"},
                    "reply_parent_message_id": {"type": "string", "description": "Message ID to reply to (optional)"},
                },
                "required": ["broadcaster_id", "sender_id", "message"],
            },
        ),
        Tool(
            name="twitch_get_chatters",
            description="Get list of users in a broadcaster's chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "first": {"type": "integer", "description": "Max number of results (max 1000)"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_send_announcement",
            description="Send an announcement message to the chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "message": {"type": "string", "description": "The announcement message"},
                    "color": {"type": "string", "description": "Color: blue, green, orange, purple, primary"},
                },
                "required": ["broadcaster_id", "moderator_id", "message"],
            },
        ),
        Tool(
            name="twitch_send_shoutout",
            description="Send a shoutout to another broadcaster",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_broadcaster_id": {"type": "string", "description": "Your broadcaster ID"},
                    "to_broadcaster_id": {"type": "string", "description": "Broadcaster to shoutout"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                },
                "required": ["from_broadcaster_id", "to_broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_get_chat_settings",
            description="Get chat settings for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_update_chat_settings",
            description="Update chat settings for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "emote_mode": {"type": "boolean", "description": "Enable emote-only mode"},
                    "follower_mode": {"type": "boolean", "description": "Enable follower-only mode"},
                    "follower_mode_duration": {"type": "integer", "description": "Minutes user must follow before chatting"},
                    "slow_mode": {"type": "boolean", "description": "Enable slow mode"},
                    "slow_mode_wait_time": {"type": "integer", "description": "Seconds between messages"},
                    "subscriber_mode": {"type": "boolean", "description": "Enable subscriber-only mode"},
                    "unique_chat_mode": {"type": "boolean", "description": "Enable unique messages only"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_get_channel_emotes",
            description="Get custom emotes for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_send_chat_message(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SendMessageRequest(**arguments)
    result = await chat.send_chat_message(sdk.http, params)
    return [TextContent(type="text", text=f"Message sent: {result.data[0].model_dump_json()}")]


async def _handle_get_chatters(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChattersRequest(**arguments)
    result = await chat.get_chatters(sdk.http, params)
    chatters = [f"{c.user_name} ({c.user_id})" for c in result.data]
    return [TextContent(type="text", text=f"Chatters ({result.total}):\n" + "\n".join(chatters[:50]))]


async def _handle_send_announcement(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SendAnnouncementRequest(**arguments)
    await chat.send_chat_announcement(sdk.http, params)
    return [TextContent(type="text", text="Announcement sent successfully")]


async def _handle_send_shoutout(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = ShoutoutRequest(**arguments)
    await chat.send_shoutout(sdk.http, params)
    return [TextContent(type="text", text="Shoutout sent successfully")]


async def _handle_get_chat_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChatSettingsRequest(**arguments)
    result = await chat.get_chat_settings(sdk.http, params)
    return [TextContent(type="text", text=result.data[0].model_dump_json(indent=2))]


async def _handle_update_chat_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateChatSettingsRequest(**arguments)
    result = await chat.update_chat_settings(sdk.http, params)
    return [TextContent(type="text", text=f"Settings updated: {result.data[0].model_dump_json()}")]


async def _handle_get_channel_emotes(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetEmotesRequest(**arguments)
    result = await chat.get_channel_emotes(sdk.http, params)
    emotes = [f"{e.name} ({e.id})" for e in result.data]
    return [TextContent(type="text", text=f"Emotes:\n" + "\n".join(emotes))]


def get_handlers() -> dict:
    """Return handlers for chat tools."""
    return {
        "twitch_send_chat_message": _handle_send_chat_message,
        "twitch_get_chatters": _handle_get_chatters,
        "twitch_send_announcement": _handle_send_announcement,
        "twitch_send_shoutout": _handle_send_shoutout,
        "twitch_get_chat_settings": _handle_get_chat_settings,
        "twitch_update_chat_settings": _handle_update_chat_settings,
        "twitch_get_channel_emotes": _handle_get_channel_emotes,
    }
