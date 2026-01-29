"""Charity MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import charity
from twitch_sdk.schemas.charity import GetCharityCampaignRequest, GetCharityDonationsRequest


def get_tools() -> list[Tool]:
    """Return charity tools."""
    return [
        Tool(
            name="twitch_get_charity_campaign",
            description="Get the broadcaster's active charity campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_get_charity_donations",
            description="Get donations to the charity campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
    ]


async def _handle_get_charity_campaign(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetCharityCampaignRequest(**arguments)
    result = await charity.get_charity_campaign(sdk.http, params)
    if not result.data:
        return [TextContent(type="text", text="No active charity campaign")]
    c = result.data[0]
    return [TextContent(type="text", text=f"Charity Campaign:\n"
        f"Charity: {c.charity_name}\n"
        f"Current: {c.current_amount.value / (10 ** c.current_amount.decimal_places)} {c.current_amount.currency}\n"
        f"Target: {c.target_amount.value / (10 ** c.target_amount.decimal_places)} {c.target_amount.currency}")]


async def _handle_get_charity_donations(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetCharityDonationsRequest(**arguments)
    result = await charity.get_charity_campaign_donations(sdk.http, params)
    donations = [f"- {d.user_name}: {d.amount.value / (10 ** d.amount.decimal_places)} {d.amount.currency}" for d in result.data]
    return [TextContent(type="text", text=f"Donations:\n" + "\n".join(donations) if donations else "No donations yet")]


def get_handlers() -> dict:
    """Return handlers for charity tools."""
    return {
        "twitch_get_charity_campaign": _handle_get_charity_campaign,
        "twitch_get_charity_donations": _handle_get_charity_donations,
    }
