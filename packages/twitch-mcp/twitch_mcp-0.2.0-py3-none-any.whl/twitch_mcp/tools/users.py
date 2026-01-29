"""Users MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import users
from twitch_sdk.schemas.users import (
    BlockUserRequest,
    GetUserBlockListRequest,
    GetUsersRequest,
    UnblockUserRequest,
    UpdateUserExtensionsRequest,
    UpdateUserRequest,
)


def get_tools() -> list[Tool]:
    """Return users tools."""
    return [
        Tool(
            name="twitch_get_users",
            description="Get user information by ID or login name",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "array", "items": {"type": "string"}, "description": "User IDs"},
                    "login": {"type": "array", "items": {"type": "string"}, "description": "User login names"},
                },
            },
        ),
        Tool(
            name="twitch_update_user",
            description="Update the authenticated user's description",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "New channel description"},
                },
            },
        ),
        Tool(
            name="twitch_get_user_block_list",
            description="Get list of users the broadcaster has blocked",
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
            name="twitch_block_user",
            description="Block a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_user_id": {"type": "string", "description": "User ID to block"},
                    "source_context": {"type": "string", "description": "Context: chat or whisper"},
                    "reason": {"type": "string", "description": "Reason: harassment, spam, or other"},
                },
                "required": ["target_user_id"],
            },
        ),
        Tool(
            name="twitch_unblock_user",
            description="Unblock a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_user_id": {"type": "string", "description": "User ID to unblock"},
                },
                "required": ["target_user_id"],
            },
        ),
        Tool(
            name="twitch_get_user_extensions",
            description="Get list of extensions the authenticated user has installed",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="twitch_get_user_active_extensions",
            description="Get user's currently active extensions",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID (omit for authenticated user)"},
                },
            },
        ),
        Tool(
            name="twitch_update_user_extensions",
            description="Update user's active extensions configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Extension config with panel, overlay, component objects"},
                },
                "required": ["data"],
            },
        ),
    ]


async def _handle_get_users(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetUsersRequest(**arguments) if arguments else None
    result = await users.get_users(sdk.http, params)
    user_list = []
    for u in result.data:
        user_list.append(
            f"- {u.display_name} ({u.login})\n"
            f"  ID: {u.id}\n"
            f"  Type: {u.broadcaster_type or 'regular'}\n"
            f"  Description: {u.description[:100]}..."
        )
    return [TextContent(type="text", text="\n".join(user_list) if user_list else "No users found")]


async def _handle_update_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateUserRequest(**arguments)
    result = await users.update_user(sdk.http, params)
    user = result.data[0]
    return [TextContent(type="text", text=f"User updated: {user.display_name}")]


async def _handle_get_user_block_list(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetUserBlockListRequest(**arguments)
    result = await users.get_user_block_list(sdk.http, params)
    blocked = [f"- {b.display_name} ({b.user_id})" for b in result.data]
    return [TextContent(type="text", text=f"Blocked users:\n" + "\n".join(blocked) if blocked else "No blocked users")]


async def _handle_block_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = BlockUserRequest(**arguments)
    await users.block_user(sdk.http, params)
    return [TextContent(type="text", text="User blocked")]


async def _handle_unblock_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UnblockUserRequest(**arguments)
    await users.unblock_user(sdk.http, params)
    return [TextContent(type="text", text="User unblocked")]


async def _handle_get_user_extensions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    result = await users.get_user_extensions(sdk.http)
    exts = [f"- {e.name} ({e.id}) v{e.version}" for e in result.data]
    return [TextContent(type="text", text=f"Installed extensions:\n" + "\n".join(exts) if exts else "No extensions installed")]


async def _handle_get_user_active_extensions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    user_id = arguments.get("user_id")
    result = await users.get_user_active_extensions(sdk.http, user_id)
    # Parse the active extensions response
    data = result.get("data", {})
    active = []
    for slot_type in ["panel", "overlay", "component"]:
        slots = data.get(slot_type, {})
        for slot_id, ext in slots.items():
            if ext.get("active"):
                active.append(f"- {slot_type}/{slot_id}: {ext.get('name', 'Unknown')}")
    return [TextContent(type="text", text=f"Active extensions:\n" + "\n".join(active) if active else "No active extensions")]


async def _handle_update_user_extensions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateUserExtensionsRequest(**arguments)
    await users.update_user_extensions(sdk.http, params)
    return [TextContent(type="text", text="User extensions updated")]


def get_handlers() -> dict:
    """Return handlers for users tools."""
    return {
        "twitch_get_users": _handle_get_users,
        "twitch_update_user": _handle_update_user,
        "twitch_get_user_block_list": _handle_get_user_block_list,
        "twitch_block_user": _handle_block_user,
        "twitch_unblock_user": _handle_unblock_user,
        "twitch_get_user_extensions": _handle_get_user_extensions,
        "twitch_get_user_active_extensions": _handle_get_user_active_extensions,
        "twitch_update_user_extensions": _handle_update_user_extensions,
    }
