"""Polls MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import polls
from twitch_sdk.schemas.polls import CreatePollRequest, EndPollRequest, GetPollsRequest, PollChoiceInput


def get_tools() -> list[Tool]:
    """Return polls tools."""
    return [
        Tool(
            name="twitch_create_poll",
            description="Create a poll on a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "title": {"type": "string", "description": "Poll title (max 60 chars)"},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of choice titles (2-5 choices, max 25 chars each)",
                    },
                    "duration": {"type": "integer", "description": "Duration in seconds (15-1800)"},
                    "channel_points_voting_enabled": {"type": "boolean", "description": "Allow channel points voting"},
                    "channel_points_per_vote": {"type": "integer", "description": "Channel points cost per vote"},
                },
                "required": ["broadcaster_id", "title", "choices", "duration"],
            },
        ),
        Tool(
            name="twitch_get_polls",
            description="Get polls for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Specific poll IDs"},
                    "first": {"type": "integer", "description": "Max results (max 20)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_end_poll",
            description="End an active poll",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "string", "description": "The poll ID"},
                    "status": {"type": "string", "description": "TERMINATED (show results) or ARCHIVED (hide results)"},
                },
                "required": ["broadcaster_id", "id", "status"],
            },
        ),
    ]


async def _handle_create_poll(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    # Convert string choices to PollChoiceInput
    choices = [PollChoiceInput(title=c) for c in arguments.pop("choices")]
    params = CreatePollRequest(choices=choices, **arguments)
    result = await polls.create_poll(sdk.http, params)
    poll = result.data[0]
    return [TextContent(type="text", text=f"Poll created!\nID: {poll.id}\nTitle: {poll.title}\nDuration: {poll.duration}s")]


async def _handle_get_polls(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetPollsRequest(**arguments)
    result = await polls.get_polls(sdk.http, params)
    poll_list = []
    for p in result.data:
        choices_str = "\n".join([f"    {c.title}: {c.votes} votes" for c in p.choices])
        poll_list.append(
            f"- {p.title} ({p.status})\n"
            f"  Choices:\n{choices_str}"
        )
    return [TextContent(type="text", text="\n".join(poll_list) if poll_list else "No polls found")]


async def _handle_end_poll(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = EndPollRequest(**arguments)
    result = await polls.end_poll(sdk.http, params)
    poll = result.data[0]
    return [TextContent(type="text", text=f"Poll ended: {poll.title} (Status: {poll.status})")]


def get_handlers() -> dict:
    """Return handlers for polls tools."""
    return {
        "twitch_create_poll": _handle_create_poll,
        "twitch_get_polls": _handle_get_polls,
        "twitch_end_poll": _handle_end_poll,
    }
