"""Schedule MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import schedule
from twitch_sdk.schemas.schedule import (
    CreateScheduleSegmentRequest,
    DeleteScheduleSegmentRequest,
    GetScheduleICalendarRequest,
    GetScheduleRequest,
    UpdateScheduleRequest,
    UpdateScheduleSegmentRequest,
)


def get_tools() -> list[Tool]:
    """Return schedule tools."""
    return [
        Tool(
            name="twitch_get_channel_schedule",
            description="Get a broadcaster's streaming schedule",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "first": {"type": "integer", "description": "Max segments (max 25)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_update_channel_schedule",
            description="Update channel schedule settings (vacation mode)",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "is_vacation_enabled": {"type": "boolean", "description": "Enable vacation mode"},
                    "vacation_start_time": {"type": "string", "description": "Vacation start (RFC3339)"},
                    "vacation_end_time": {"type": "string", "description": "Vacation end (RFC3339)"},
                    "timezone": {"type": "string", "description": "Timezone (e.g., America/New_York)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_create_schedule_segment",
            description="Create a scheduled stream segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "start_time": {"type": "string", "description": "Start time (RFC3339)"},
                    "timezone": {"type": "string", "description": "Timezone (e.g., America/New_York)"},
                    "duration": {"type": "integer", "description": "Duration in minutes (30-1440)"},
                    "is_recurring": {"type": "boolean", "description": "Whether this is weekly recurring"},
                    "category_id": {"type": "string", "description": "Game/category ID"},
                    "title": {"type": "string", "description": "Stream title"},
                },
                "required": ["broadcaster_id", "start_time", "timezone", "duration"],
            },
        ),
        Tool(
            name="twitch_delete_schedule_segment",
            description="Delete a scheduled stream segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "string", "description": "Segment ID to delete"},
                },
                "required": ["broadcaster_id", "id"],
            },
        ),
        Tool(
            name="twitch_get_schedule_icalendar",
            description="Get a broadcaster's schedule as iCalendar data",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_update_schedule_segment",
            description="Update a scheduled stream segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "string", "description": "Segment ID to update"},
                    "start_time": {"type": "string", "description": "New start time (RFC3339)"},
                    "timezone": {"type": "string", "description": "Timezone (e.g., America/New_York)"},
                    "duration": {"type": "integer", "description": "Duration in minutes (30-1440)"},
                    "is_canceled": {"type": "boolean", "description": "Cancel this segment"},
                    "category_id": {"type": "string", "description": "Game/category ID"},
                    "title": {"type": "string", "description": "Stream title (max 140 chars)"},
                },
                "required": ["broadcaster_id", "id"],
            },
        ),
    ]


async def _handle_get_channel_schedule(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetScheduleRequest(**arguments)
    result = await schedule.get_channel_stream_schedule(sdk.http, params)
    sched = result.get("data", {})
    segments = sched.get("segments", [])
    seg_list = []
    for s in segments:
        seg_list.append(f"- {s.get('title', 'Untitled')}\n  {s.get('start_time')} - {s.get('end_time')}")
    return [TextContent(type="text", text=f"Schedule:\n" + "\n".join(seg_list) if seg_list else "No scheduled streams")]


async def _handle_update_channel_schedule(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateScheduleRequest(**arguments)
    await schedule.update_channel_stream_schedule(sdk.http, params)
    return [TextContent(type="text", text="Schedule settings updated")]


async def _handle_create_schedule_segment(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = CreateScheduleSegmentRequest(**arguments)
    result = await schedule.create_channel_stream_schedule_segment(sdk.http, params)
    return [TextContent(type="text", text="Schedule segment created")]


async def _handle_delete_schedule_segment(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = DeleteScheduleSegmentRequest(**arguments)
    await schedule.delete_channel_stream_schedule_segment(sdk.http, params)
    return [TextContent(type="text", text="Schedule segment deleted")]


async def _handle_get_schedule_icalendar(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetScheduleICalendarRequest(**arguments)
    result = await schedule.get_channel_icalendar(sdk.http, params)
    # Result is iCalendar text data
    return [TextContent(type="text", text=f"iCalendar data:\n{result[:2000]}..." if len(str(result)) > 2000 else f"iCalendar data:\n{result}")]


async def _handle_update_schedule_segment(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = UpdateScheduleSegmentRequest(**arguments)
    result = await schedule.update_channel_stream_schedule_segment(sdk.http, params)
    return [TextContent(type="text", text="Schedule segment updated")]


def get_handlers() -> dict:
    """Return handlers for schedule tools."""
    return {
        "twitch_get_channel_schedule": _handle_get_channel_schedule,
        "twitch_update_channel_schedule": _handle_update_channel_schedule,
        "twitch_create_schedule_segment": _handle_create_schedule_segment,
        "twitch_delete_schedule_segment": _handle_delete_schedule_segment,
        "twitch_get_schedule_icalendar": _handle_get_schedule_icalendar,
        "twitch_update_schedule_segment": _handle_update_schedule_segment,
    }
