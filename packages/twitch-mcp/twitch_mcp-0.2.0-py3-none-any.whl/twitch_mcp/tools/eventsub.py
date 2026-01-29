"""EventSub MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import eventsub
from twitch_sdk.schemas.eventsub import (
    CreateConduitRequest,
    CreateEventSubSubscriptionRequest,
    DeleteConduitRequest,
    DeleteEventSubSubscriptionRequest,
    GetConduitShardsRequest,
    GetEventSubSubscriptionsRequest,
    UpdateConduitRequest,
    UpdateConduitShardsRequest,
)


def get_tools() -> list[Tool]:
    """Return eventsub tools."""
    return [
        Tool(
            name="twitch_get_eventsub_subscriptions",
            description="Get list of EventSub subscriptions",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status"},
                    "type": {"type": "string", "description": "Filter by event type"},
                    "user_id": {"type": "string", "description": "Filter by user ID"},
                },
            },
        ),
        Tool(
            name="twitch_create_eventsub_subscription",
            description="Create an EventSub subscription (webhook)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Event type (e.g., channel.follow)"},
                    "version": {"type": "string", "description": "Subscription version"},
                    "condition": {"type": "object", "description": "Subscription condition"},
                    "transport": {"type": "object", "description": "Transport config (method, callback, secret)"},
                },
                "required": ["type", "version", "condition", "transport"],
            },
        ),
        Tool(
            name="twitch_delete_eventsub_subscription",
            description="Delete an EventSub subscription",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Subscription ID to delete"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="twitch_get_conduits",
            description="Get list of conduits for event distribution",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="twitch_create_conduit",
            description="Create a conduit for distributing events across shards",
            inputSchema={
                "type": "object",
                "properties": {
                    "shard_count": {"type": "integer", "description": "Number of shards (min 1)"},
                },
                "required": ["shard_count"],
            },
        ),
        Tool(
            name="twitch_update_conduit",
            description="Update a conduit's shard count",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Conduit ID"},
                    "shard_count": {"type": "integer", "description": "New shard count (min 1)"},
                },
                "required": ["id", "shard_count"],
            },
        ),
        Tool(
            name="twitch_delete_conduit",
            description="Delete a conduit",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Conduit ID to delete"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="twitch_get_conduit_shards",
            description="Get shards for a conduit",
            inputSchema={
                "type": "object",
                "properties": {
                    "conduit_id": {"type": "string", "description": "Conduit ID"},
                    "status": {"type": "string", "description": "Filter by status"},
                },
                "required": ["conduit_id"],
            },
        ),
        Tool(
            name="twitch_update_conduit_shards",
            description="Update conduit shards (configure transport for each shard)",
            inputSchema={
                "type": "object",
                "properties": {
                    "conduit_id": {"type": "string", "description": "Conduit ID"},
                    "shards": {"type": "array", "description": "Array of shard configs with id and transport"},
                },
                "required": ["conduit_id", "shards"],
            },
        ),
    ]


async def _handle_get_eventsub_subscriptions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetEventSubSubscriptionsRequest(**arguments) if arguments else None
    result = await eventsub.get_eventsub_subscriptions(sdk.http, params)
    subs = []
    for s in result.data:
        subs.append(f"- {s.type} ({s.status})\n  ID: {s.id}")
    return [TextContent(type="text", text=f"EventSub Subscriptions ({result.total}, cost: {result.total_cost}/{result.max_total_cost}):\n" + "\n".join(subs))]


async def _handle_create_eventsub_subscription(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateEventSubSubscriptionRequest(**arguments)
    result = await eventsub.create_eventsub_subscription(sdk.http, params)
    sub = result.data[0]
    return [TextContent(type="text", text=f"Subscription created:\nID: {sub.id}\nType: {sub.type}\nStatus: {sub.status}")]


async def _handle_delete_eventsub_subscription(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteEventSubSubscriptionRequest(**arguments)
    await eventsub.delete_eventsub_subscription(sdk.http, params)
    return [TextContent(type="text", text="Subscription deleted")]


async def _handle_get_conduits(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    result = await eventsub.get_conduits(sdk.http)
    conduits = [f"- ID: {c.id} (shards: {c.shard_count})" for c in result.data]
    return [TextContent(type="text", text=f"Conduits:\n" + "\n".join(conduits) if conduits else "No conduits")]


async def _handle_create_conduit(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateConduitRequest(**arguments)
    result = await eventsub.create_conduit(sdk.http, params)
    conduit = result.data[0]
    return [TextContent(type="text", text=f"Conduit created:\nID: {conduit.id}\nShards: {conduit.shard_count}")]


async def _handle_update_conduit(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateConduitRequest(**arguments)
    result = await eventsub.update_conduit(sdk.http, params)
    conduit = result.data[0]
    return [TextContent(type="text", text=f"Conduit updated: {conduit.shard_count} shards")]


async def _handle_delete_conduit(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteConduitRequest(**arguments)
    await eventsub.delete_conduit(sdk.http, params)
    return [TextContent(type="text", text="Conduit deleted")]


async def _handle_get_conduit_shards(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetConduitShardsRequest(**arguments)
    result = await eventsub.get_conduit_shards(sdk.http, params)
    shards = [f"- Shard {s.id}: {s.status} ({s.transport.method})" for s in result.data]
    return [TextContent(type="text", text=f"Conduit Shards:\n" + "\n".join(shards) if shards else "No shards")]


async def _handle_update_conduit_shards(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateConduitShardsRequest(**arguments)
    result = await eventsub.update_conduit_shards(sdk.http, params)
    return [TextContent(type="text", text=f"Updated {len(result.data)} shards")]


def get_handlers() -> dict:
    """Return handlers for eventsub tools."""
    return {
        "twitch_get_eventsub_subscriptions": _handle_get_eventsub_subscriptions,
        "twitch_create_eventsub_subscription": _handle_create_eventsub_subscription,
        "twitch_delete_eventsub_subscription": _handle_delete_eventsub_subscription,
        "twitch_get_conduits": _handle_get_conduits,
        "twitch_create_conduit": _handle_create_conduit,
        "twitch_update_conduit": _handle_update_conduit,
        "twitch_delete_conduit": _handle_delete_conduit,
        "twitch_get_conduit_shards": _handle_get_conduit_shards,
        "twitch_update_conduit_shards": _handle_update_conduit_shards,
    }
