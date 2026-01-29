"""Guest Star MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import guest_star
from twitch_sdk.schemas.guest_star import (
    AssignGuestStarSlotRequest,
    CreateGuestStarSessionRequest,
    DeleteGuestStarInviteRequest,
    DeleteGuestStarSlotRequest,
    EndGuestStarSessionRequest,
    GetGuestStarInvitesRequest,
    GetGuestStarSessionRequest,
    GetGuestStarSettingsRequest,
    SendGuestStarInviteRequest,
    UpdateGuestStarSettingsRequest,
    UpdateGuestStarSlotRequest,
    UpdateGuestStarSlotSettingsRequest,
)


def get_tools() -> list[Tool]:
    """Return guest star tools."""
    return [
        Tool(
            name="twitch_get_guest_star_settings",
            description="Get guest star settings for a channel",
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
            name="twitch_get_guest_star_session",
            description="Get active guest star session",
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
            name="twitch_create_guest_star_session",
            description="Create a guest star session",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_end_guest_star_session",
            description="End a guest star session",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                },
                "required": ["broadcaster_id", "session_id"],
            },
        ),
        Tool(
            name="twitch_send_guest_star_invite",
            description="Send a guest star invite",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "guest_id": {"type": "string", "description": "User ID to invite"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "guest_id"],
            },
        ),
        Tool(
            name="twitch_update_guest_star_settings",
            description="Update guest star settings for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "is_moderator_send_live_enabled": {"type": "boolean", "description": "Allow mods to send guests live"},
                    "slot_count": {"type": "integer", "description": "Number of slots (1-6)"},
                    "is_browser_source_audio_enabled": {"type": "boolean", "description": "Enable browser source audio"},
                    "group_layout": {"type": "string", "description": "Layout: TILED_LAYOUT, SCREENSHARE_LAYOUT, HORIZONTAL_LAYOUT, VERTICAL_LAYOUT"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_get_guest_star_invites",
            description="Get pending guest star invites for a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id"],
            },
        ),
        Tool(
            name="twitch_delete_guest_star_invite",
            description="Revoke a pending guest star invite",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "guest_id": {"type": "string", "description": "User ID of invited guest"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "guest_id"],
            },
        ),
        Tool(
            name="twitch_assign_guest_star_slot",
            description="Assign a guest to a slot",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "guest_id": {"type": "string", "description": "User ID of the guest"},
                    "slot_id": {"type": "string", "description": "Slot ID to assign to"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "guest_id", "slot_id"],
            },
        ),
        Tool(
            name="twitch_update_guest_star_slot",
            description="Move a guest between slots",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "source_slot_id": {"type": "string", "description": "Current slot ID"},
                    "destination_slot_id": {"type": "string", "description": "Target slot ID (omit to remove from slot)"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "source_slot_id"],
            },
        ),
        Tool(
            name="twitch_delete_guest_star_slot",
            description="Remove a guest from their slot",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "guest_id": {"type": "string", "description": "User ID of the guest"},
                    "slot_id": {"type": "string", "description": "Slot ID"},
                    "should_reinvite_guest": {"type": "boolean", "description": "Re-invite the guest after removal"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "guest_id", "slot_id"],
            },
        ),
        Tool(
            name="twitch_update_guest_star_slot_settings",
            description="Update slot settings (audio, video, volume, live status)",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "moderator_id": {"type": "string", "description": "The moderator's user ID"},
                    "session_id": {"type": "string", "description": "The session ID"},
                    "slot_id": {"type": "string", "description": "Slot ID"},
                    "is_audio_enabled": {"type": "boolean", "description": "Enable/disable audio"},
                    "is_video_enabled": {"type": "boolean", "description": "Enable/disable video"},
                    "is_live": {"type": "boolean", "description": "Set live status"},
                    "volume": {"type": "integer", "description": "Volume level (0-100)"},
                },
                "required": ["broadcaster_id", "moderator_id", "session_id", "slot_id"],
            },
        ),
    ]


async def _handle_get_guest_star_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGuestStarSettingsRequest(**arguments)
    result = await guest_star.get_channel_guest_star_settings(sdk.http, params)
    settings = result.data[0]
    return [TextContent(type="text", text=f"Guest Star Settings:\n"
        f"Slot count: {settings.slot_count}\n"
        f"Browser audio: {settings.is_browser_source_audio_enabled}\n"
        f"Layout: {settings.group_layout}")]


async def _handle_get_guest_star_session(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGuestStarSessionRequest(**arguments)
    result = await guest_star.get_guest_star_session(sdk.http, params)
    if not result.data:
        return [TextContent(type="text", text="No active guest star session")]
    session = result.data[0]
    guests = [f"  - {g.user_display_name} (slot {g.slot_id})" for g in session.guests]
    return [TextContent(type="text", text=f"Session ID: {session.id}\nGuests:\n" + "\n".join(guests))]


async def _handle_create_guest_star_session(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateGuestStarSessionRequest(**arguments)
    result = await guest_star.create_guest_star_session(sdk.http, params)
    session = result.data[0]
    return [TextContent(type="text", text=f"Guest star session created: {session.id}")]


async def _handle_end_guest_star_session(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = EndGuestStarSessionRequest(**arguments)
    await guest_star.end_guest_star_session(sdk.http, params)
    return [TextContent(type="text", text="Guest star session ended")]


async def _handle_send_guest_star_invite(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = SendGuestStarInviteRequest(**arguments)
    await guest_star.send_guest_star_invite(sdk.http, params)
    return [TextContent(type="text", text="Guest star invite sent")]


async def _handle_update_guest_star_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateGuestStarSettingsRequest(**arguments)
    await guest_star.update_channel_guest_star_settings(sdk.http, params)
    return [TextContent(type="text", text="Guest star settings updated")]


async def _handle_get_guest_star_invites(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetGuestStarInvitesRequest(**arguments)
    result = await guest_star.get_guest_star_invites(sdk.http, params)
    invites = [f"- {i.user_id}: {i.status}" for i in result.data]
    return [TextContent(type="text", text=f"Invites:\n" + "\n".join(invites) if invites else "No pending invites")]


async def _handle_delete_guest_star_invite(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteGuestStarInviteRequest(**arguments)
    await guest_star.delete_guest_star_invite(sdk.http, params)
    return [TextContent(type="text", text="Guest star invite revoked")]


async def _handle_assign_guest_star_slot(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = AssignGuestStarSlotRequest(**arguments)
    await guest_star.assign_guest_star_slot(sdk.http, params)
    return [TextContent(type="text", text=f"Guest assigned to slot {arguments.get('slot_id')}")]


async def _handle_update_guest_star_slot(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateGuestStarSlotRequest(**arguments)
    await guest_star.update_guest_star_slot(sdk.http, params)
    return [TextContent(type="text", text="Guest slot updated")]


async def _handle_delete_guest_star_slot(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteGuestStarSlotRequest(**arguments)
    await guest_star.delete_guest_star_slot(sdk.http, params)
    return [TextContent(type="text", text="Guest removed from slot")]


async def _handle_update_guest_star_slot_settings(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateGuestStarSlotSettingsRequest(**arguments)
    await guest_star.update_guest_star_slot_settings(sdk.http, params)
    return [TextContent(type="text", text="Slot settings updated")]


def get_handlers() -> dict:
    """Return handlers for guest star tools."""
    return {
        "twitch_get_guest_star_settings": _handle_get_guest_star_settings,
        "twitch_get_guest_star_session": _handle_get_guest_star_session,
        "twitch_create_guest_star_session": _handle_create_guest_star_session,
        "twitch_end_guest_star_session": _handle_end_guest_star_session,
        "twitch_send_guest_star_invite": _handle_send_guest_star_invite,
        "twitch_update_guest_star_settings": _handle_update_guest_star_settings,
        "twitch_get_guest_star_invites": _handle_get_guest_star_invites,
        "twitch_delete_guest_star_invite": _handle_delete_guest_star_invite,
        "twitch_assign_guest_star_slot": _handle_assign_guest_star_slot,
        "twitch_update_guest_star_slot": _handle_update_guest_star_slot,
        "twitch_delete_guest_star_slot": _handle_delete_guest_star_slot,
        "twitch_update_guest_star_slot_settings": _handle_update_guest_star_slot_settings,
    }
