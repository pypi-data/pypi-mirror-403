"""Goals MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import goals
from twitch_sdk.schemas.goals import GetGoalsRequest


def get_tools() -> list[Tool]:
    """Return goals tools."""
    return [
        Tool(
            name="twitch_get_creator_goals",
            description="Get the broadcaster's active creator goals",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_get_creator_goals(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGoalsRequest(**arguments)
    result = await goals.get_creator_goals(sdk.http, params)
    goal_list = []
    for g in result.data:
        goal_list.append(f"- {g.description}\n  Type: {g.type}\n  Progress: {g.current_amount}/{g.target_amount}")
    return [TextContent(type="text", text=f"Creator Goals:\n" + "\n".join(goal_list) if goal_list else "No active goals")]


def get_handlers() -> dict:
    """Return handlers for goals tools."""
    return {
        "twitch_get_creator_goals": _handle_get_creator_goals,
    }
