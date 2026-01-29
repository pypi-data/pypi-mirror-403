"""Teams MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import teams
from twitch_sdk.schemas.teams import GetChannelTeamsRequest, GetTeamsRequest


def get_tools() -> list[Tool]:
    """Return teams tools."""
    return [
        Tool(
            name="twitch_get_teams",
            description="Get team information by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Team name"},
                    "id": {"type": "string", "description": "Team ID"},
                },
            },
        ),
        Tool(
            name="twitch_get_channel_teams",
            description="Get teams that a broadcaster is a member of",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_get_teams(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetTeamsRequest(**arguments)
    result = await teams.get_teams(sdk.http, params)
    team_list = []
    for t in result.data:
        members = len(t.users) if t.users else 0
        team_list.append(f"- {t.team_display_name} ({members} members)\n  {t.info[:100]}...")
    return [TextContent(type="text", text="\n".join(team_list) if team_list else "No teams found")]


async def _handle_get_channel_teams(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetChannelTeamsRequest(**arguments)
    result = await teams.get_channel_teams(sdk.http, params)
    team_list = [f"- {t.team_display_name}" for t in result.data]
    return [TextContent(type="text", text=f"Channel Teams:\n" + "\n".join(team_list) if team_list else "Not on any teams")]


def get_handlers() -> dict:
    """Return handlers for teams tools."""
    return {
        "twitch_get_teams": _handle_get_teams,
        "twitch_get_channel_teams": _handle_get_channel_teams,
    }
