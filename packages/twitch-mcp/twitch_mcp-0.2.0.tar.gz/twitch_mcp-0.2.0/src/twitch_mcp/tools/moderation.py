"""Moderation MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import moderation
from twitch_sdk.schemas.moderation import (
    AddBlockedTermRequest,
    AddModeratorRequest,
    BanUserData,
    BanUserRequest,
    DeleteChatMessagesRequest,
    GetAutoModSettingsRequest,
    GetBannedUsersRequest,
    GetBlockedTermsRequest,
    GetModeratorsRequest,
    GetShieldModeStatusRequest,
    GetUnbanRequestsRequest,
    ManageHeldAutoModMessageRequest,
    RemoveBlockedTermRequest,
    RemoveModeratorRequest,
    ResolveUnbanRequestRequest,
    UnbanUserRequest,
    UpdateAutoModSettingsRequest,
    UpdateShieldModeStatusRequest,
    WarnUserRequest,
)


def get_tools() -> list[Tool]:
    """Return moderation tools."""
    return [
        Tool(
            name="twitch_ban_user",
            description="Ban a user from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "user_id": {"type": "string", "description": "User ID to ban"},
                    "duration": {"type": "integer", "description": "Timeout duration in seconds (omit for permanent)"},
                    "reason": {"type": "string", "description": "Reason for the ban"},
                },
                "required": ["broadcaster_id", "moderator_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_unban_user",
            description="Unban a user from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "user_id": {"type": "string", "description": "User ID to unban"},
                },
                "required": ["broadcaster_id", "moderator_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_get_banned_users",
            description="Get list of banned users",
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
            name="twitch_warn_user",
            description="Send a warning to a user in chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "user_id": {"type": "string", "description": "User ID to warn"},
                    "reason": {"type": "string", "description": "Reason for the warning"},
                },
                "required": ["broadcaster_id", "moderator_id", "user_id", "reason"],
            },
        ),
        Tool(
            name="twitch_delete_chat_messages",
            description="Delete chat messages (specific message or all)",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "message_id": {"type": "string", "description": "Specific message ID to delete (omit to clear all)"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_get_moderators",
            description="Get list of moderators for a channel",
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
            name="twitch_add_moderator",
            description="Add a moderator to the channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "string", "description": "User ID to make moderator"},
                },
                "required": ["broadcaster_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_remove_moderator",
            description="Remove a moderator from the channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "user_id": {"type": "string", "description": "User ID to remove as moderator"},
                },
                "required": ["broadcaster_id", "user_id"],
            },
        ),
        Tool(
            name="twitch_get_blocked_terms",
            description="Get list of blocked terms",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_add_blocked_term",
            description="Add a blocked term",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "text": {"type": "string", "description": "Term to block (2-500 chars)"},
                },
                "required": ["broadcaster_id", "moderator_id", "text"],
            },
        ),
        Tool(
            name="twitch_get_shield_mode_status",
            description="Get shield mode status",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_update_shield_mode",
            description="Enable or disable shield mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "is_active": {"type": "boolean", "description": "True to enable, false to disable"},
                },
                "required": ["broadcaster_id", "moderator_id", "is_active"],
            },
        ),
        Tool(
            name="twitch_get_unban_requests",
            description="Get pending unban requests for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "status": {"type": "string", "description": "Filter by status: pending, approved, denied, acknowledged, canceled"},
                    "user_id": {"type": "string", "description": "Filter by user ID"},
                    "first": {"type": "integer", "description": "Max results (max 100)"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_resolve_unban_request",
            description="Approve or deny an unban request",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "unban_request_id": {"type": "string", "description": "The unban request ID"},
                    "status": {"type": "string", "description": "approved or denied"},
                    "resolution_text": {"type": "string", "description": "Optional resolution message"},
                },
                "required": ["broadcaster_id", "moderator_id", "unban_request_id", "status"],
            },
        ),
        Tool(
            name="twitch_remove_blocked_term",
            description="Remove a blocked term from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "id": {"type": "string", "description": "The blocked term ID to remove"},
                },
                "required": ["broadcaster_id", "moderator_id", "id"],
            },
        ),
        Tool(
            name="twitch_get_automod_settings",
            description="Get AutoMod settings for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_update_automod_settings",
            description="Update AutoMod settings for a channel (levels 0-4)",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "overall_level": {"type": "integer", "description": "Overall level (0-4), overrides individual settings"},
                    "aggression": {"type": "integer", "description": "Aggression filter level (0-4)"},
                    "bullying": {"type": "integer", "description": "Bullying filter level (0-4)"},
                    "disability": {"type": "integer", "description": "Disability filter level (0-4)"},
                    "misogyny": {"type": "integer", "description": "Misogyny filter level (0-4)"},
                    "race_ethnicity_or_religion": {"type": "integer", "description": "Race/ethnicity/religion filter (0-4)"},
                    "sex_based_terms": {"type": "integer", "description": "Sex-based terms filter (0-4)"},
                    "sexuality_sex_or_gender": {"type": "integer", "description": "Sexuality/gender filter (0-4)"},
                    "swearing": {"type": "integer", "description": "Swearing filter level (0-4)"},
                },
                "required": ["broadcaster_id", "moderator_id"],
            },
        ),
        Tool(
            name="twitch_manage_held_automod_message",
            description="Allow or deny a message held by AutoMod",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The moderator's user ID"},
                    "msg_id": {"type": "string", "description": "The held message ID"},
                    "action": {"type": "string", "description": "ALLOW or DENY"},
                },
                "required": ["user_id", "msg_id", "action"],
            },
        ),
    ]


async def _handle_ban_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    ban_data = BanUserData(
        user_id=arguments.pop("user_id"),
        duration=arguments.pop("duration", None),
        reason=arguments.pop("reason", None),
    )
    params = BanUserRequest(data=ban_data, **arguments)
    result = await moderation.ban_user(sdk.http, params)
    ban = result.data[0]
    return [TextContent(type="text", text=f"User {ban.user_id} banned until {ban.end_time or 'permanent'}")]


async def _handle_unban_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UnbanUserRequest(**arguments)
    await moderation.unban_user(sdk.http, params)
    return [TextContent(type="text", text="User unbanned successfully")]


async def _handle_get_banned_users(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetBannedUsersRequest(**arguments)
    result = await moderation.get_banned_users(sdk.http, params)
    banned = [f"- {b.user_name}: {b.reason or 'No reason'} (expires: {b.expires_at or 'never'})" for b in result.data]
    return [TextContent(type="text", text=f"Banned users:\n" + "\n".join(banned) if banned else "No banned users")]


async def _handle_warn_user(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = WarnUserRequest(**arguments)
    await moderation.warn_chat_user(sdk.http, params)
    return [TextContent(type="text", text="Warning sent")]


async def _handle_delete_chat_messages(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteChatMessagesRequest(**arguments)
    await moderation.delete_chat_messages(sdk.http, params)
    msg = "Specific message deleted" if arguments.get("message_id") else "All chat messages cleared"
    return [TextContent(type="text", text=msg)]


async def _handle_get_moderators(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetModeratorsRequest(**arguments)
    result = await moderation.get_moderators(sdk.http, params)
    mods = [f"- {m.user_name}" for m in result.data]
    return [TextContent(type="text", text=f"Moderators:\n" + "\n".join(mods) if mods else "No moderators")]


async def _handle_add_moderator(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = AddModeratorRequest(**arguments)
    await moderation.add_moderator(sdk.http, params)
    return [TextContent(type="text", text="Moderator added")]


async def _handle_remove_moderator(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = RemoveModeratorRequest(**arguments)
    await moderation.remove_moderator(sdk.http, params)
    return [TextContent(type="text", text="Moderator removed")]


async def _handle_get_blocked_terms(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetBlockedTermsRequest(**arguments)
    result = await moderation.get_blocked_terms(sdk.http, params)
    terms = [f"- {t.text}" for t in result.data]
    return [TextContent(type="text", text=f"Blocked terms:\n" + "\n".join(terms) if terms else "No blocked terms")]


async def _handle_add_blocked_term(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = AddBlockedTermRequest(**arguments)
    result = await moderation.add_blocked_term(sdk.http, params)
    return [TextContent(type="text", text=f"Blocked term added: {result.data[0].text}")]


async def _handle_get_shield_mode_status(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetShieldModeStatusRequest(**arguments)
    result = await moderation.get_shield_mode_status(sdk.http, params)
    status = result.data[0]
    return [TextContent(type="text", text=f"Shield mode: {'ACTIVE' if status.is_active else 'INACTIVE'}")]


async def _handle_update_shield_mode(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateShieldModeStatusRequest(**arguments)
    result = await moderation.update_shield_mode_status(sdk.http, params)
    status = result.data[0]
    return [TextContent(type="text", text=f"Shield mode {'enabled' if status.is_active else 'disabled'}")]


async def _handle_get_unban_requests(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetUnbanRequestsRequest(**arguments)
    result = await moderation.get_unban_requests(sdk.http, params)
    requests = [f"- {r.user_name}: {r.text} ({r.status})" for r in result.data]
    return [TextContent(type="text", text=f"Unban requests:\n" + "\n".join(requests) if requests else "No unban requests")]


async def _handle_resolve_unban_request(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = ResolveUnbanRequestRequest(**arguments)
    result = await moderation.resolve_unban_request(sdk.http, params)
    req = result.data[0]
    return [TextContent(type="text", text=f"Unban request {req.status}: {req.user_name}")]


async def _handle_remove_blocked_term(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = RemoveBlockedTermRequest(**arguments)
    await moderation.remove_blocked_term(sdk.http, params)
    return [TextContent(type="text", text="Blocked term removed")]


async def _handle_get_automod_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetAutoModSettingsRequest(**arguments)
    result = await moderation.get_automod_settings(sdk.http, params)
    s = result.data[0]
    text = (f"AutoMod Settings:\n"
            f"Overall: {s.overall_level or 'custom'}\n"
            f"Aggression: {s.aggression}, Bullying: {s.bullying}\n"
            f"Disability: {s.disability}, Misogyny: {s.misogyny}\n"
            f"Race/Religion: {s.race_ethnicity_or_religion}\n"
            f"Sex terms: {s.sex_based_terms}, Sexuality: {s.sexuality_sex_or_gender}\n"
            f"Swearing: {s.swearing}")
    return [TextContent(type="text", text=text)]


async def _handle_update_automod_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateAutoModSettingsRequest(**arguments)
    result = await moderation.update_automod_settings(sdk.http, params)
    return [TextContent(type="text", text="AutoMod settings updated")]


async def _handle_manage_held_automod_message(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = ManageHeldAutoModMessageRequest(**arguments)
    await moderation.manage_held_automod_message(sdk.http, params)
    action = arguments.get("action", "processed")
    return [TextContent(type="text", text=f"Message {action.lower()}ed")]


def get_handlers() -> dict:
    """Return handlers for moderation tools."""
    return {
        "twitch_ban_user": _handle_ban_user,
        "twitch_unban_user": _handle_unban_user,
        "twitch_get_banned_users": _handle_get_banned_users,
        "twitch_warn_user": _handle_warn_user,
        "twitch_delete_chat_messages": _handle_delete_chat_messages,
        "twitch_get_moderators": _handle_get_moderators,
        "twitch_add_moderator": _handle_add_moderator,
        "twitch_remove_moderator": _handle_remove_moderator,
        "twitch_get_blocked_terms": _handle_get_blocked_terms,
        "twitch_add_blocked_term": _handle_add_blocked_term,
        "twitch_get_shield_mode_status": _handle_get_shield_mode_status,
        "twitch_update_shield_mode": _handle_update_shield_mode,
        "twitch_get_unban_requests": _handle_get_unban_requests,
        "twitch_resolve_unban_request": _handle_resolve_unban_request,
        "twitch_remove_blocked_term": _handle_remove_blocked_term,
        "twitch_get_automod_settings": _handle_get_automod_settings,
        "twitch_update_automod_settings": _handle_update_automod_settings,
        "twitch_manage_held_automod_message": _handle_manage_held_automod_message,
    }
