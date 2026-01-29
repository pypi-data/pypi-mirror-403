"""Whispers MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import whispers
from twitch_sdk.schemas.whispers import SendWhisperRequest


def get_tools() -> list[Tool]:
    """Return whispers tools."""
    return [
        Tool(
            name="twitch_send_whisper",
            description="Send a whisper (private message) to another user",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_user_id": {"type": "string", "description": "Your user ID"},
                    "to_user_id": {"type": "string", "description": "Recipient's user ID"},
                    "message": {"type": "string", "description": "Message to send (max 10000 chars)"},
                },
                "required": ["from_user_id", "to_user_id", "message"],
            },
        ),
    ]


async def _handle_send_whisper(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SendWhisperRequest(**arguments)
    await whispers.send_whisper(sdk.http, params)
    return [TextContent(type="text", text="Whisper sent")]


def get_handlers() -> dict:
    """Return handlers for whispers tools."""
    return {
        "twitch_send_whisper": _handle_send_whisper,
    }
