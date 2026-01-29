"""Subscriptions MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import subscriptions
from twitch_sdk.schemas.subscriptions import CheckUserSubscriptionRequest, GetBroadcasterSubscriptionsRequest


def get_tools() -> list[Tool]:
    """Return subscriptions tools."""
    return [
        Tool(
            name="twitch_get_broadcaster_subscriptions",
            description="Get list of subscribers for a broadcaster",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "array", "items": {"type": "string"}, "description": "Filter to specific users"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_check_user_subscription",
            description="Check if a user is subscribed to a broadcaster",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "string", "description": "The user ID to check"},
                },
                "required": ["broadcaster_id", "user_id"],
            },
        ),
    ]


async def _handle_get_broadcaster_subscriptions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetBroadcasterSubscriptionsRequest(**arguments)
    result = await subscriptions.get_broadcaster_subscriptions(sdk.http, params)
    subs = [f"- {s.user_name} (Tier {s.tier})" + (" [Gift]" if s.is_gift else "") for s in result.data]
    return [TextContent(type="text", text=f"Subscribers ({result.total}, {result.points} points):\n" + "\n".join(subs[:50]))]


async def _handle_check_user_subscription(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CheckUserSubscriptionRequest(**arguments)
    try:
        result = await subscriptions.check_user_subscription(sdk.http, params)
        sub = result.data[0]
        return [TextContent(type="text", text=f"User is subscribed at Tier {sub.tier}" + (" (Gift)" if sub.is_gift else ""))]
    except Exception:
        return [TextContent(type="text", text="User is not subscribed")]


def get_handlers() -> dict:
    """Return handlers for subscriptions tools."""
    return {
        "twitch_get_broadcaster_subscriptions": _handle_get_broadcaster_subscriptions,
        "twitch_check_user_subscription": _handle_check_user_subscription,
    }
