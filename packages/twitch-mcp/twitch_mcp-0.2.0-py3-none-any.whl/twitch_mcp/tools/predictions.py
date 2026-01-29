"""Predictions MCP tools."""

from mcp.types import Tool, TextContent

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints import predictions
from twitch_sdk.schemas.predictions import (
    CreatePredictionRequest,
    EndPredictionRequest,
    GetPredictionsRequest,
    PredictionOutcomeInput,
)


def get_tools() -> list[Tool]:
    """Return predictions tools."""
    return [
        Tool(
            name="twitch_create_prediction",
            description="Create a prediction on a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "title": {"type": "string", "description": "Prediction title (max 45 chars)"},
                    "outcomes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of outcome titles (2-10 outcomes, max 25 chars each)",
                    },
                    "prediction_window": {"type": "integer", "description": "Seconds users can make predictions (30-1800)"},
                },
                "required": ["broadcaster_id", "title", "outcomes", "prediction_window"],
            },
        ),
        Tool(
            name="twitch_get_predictions",
            description="Get predictions for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "array", "items": {"type": "string"}, "description": "Specific prediction IDs"},
                    "first": {"type": "integer", "description": "Max results (max 25)"},
                },
                "required": ["broadcaster_id"],
            },
        ),
        Tool(
            name="twitch_end_prediction",
            description="End/resolve a prediction",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcaster_id": {"type": "string", "description": "The broadcaster's user ID"},
                    "id": {"type": "string", "description": "The prediction ID"},
                    "status": {"type": "string", "description": "RESOLVED, CANCELED, or LOCKED"},
                    "winning_outcome_id": {"type": "string", "description": "The winning outcome ID (required for RESOLVED)"},
                },
                "required": ["broadcaster_id", "id", "status"],
            },
        ),
    ]


async def _handle_create_prediction(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    # Convert string outcomes to PredictionOutcomeInput
    outcomes = [PredictionOutcomeInput(title=o) for o in arguments.pop("outcomes")]
    params = CreatePredictionRequest(outcomes=outcomes, **arguments)
    result = await predictions.create_prediction(sdk.http, params)
    pred = result.data[0]
    outcomes_str = ", ".join([f"{o.title} ({o.id})" for o in pred.outcomes])
    return [TextContent(type="text", text=f"Prediction created!\nID: {pred.id}\nTitle: {pred.title}\nOutcomes: {outcomes_str}")]


async def _handle_get_predictions(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = GetPredictionsRequest(**arguments)
    result = await predictions.get_predictions(sdk.http, params)
    pred_list = []
    for p in result.data:
        outcomes_str = "\n".join([f"    {o.title}: {o.channel_points} points ({o.users} users)" for o in p.outcomes])
        pred_list.append(
            f"- {p.title} ({p.status})\n"
            f"  Outcomes:\n{outcomes_str}"
        )
    return [TextContent(type="text", text="\n".join(pred_list) if pred_list else "No predictions found")]


async def _handle_end_prediction(sdk: TwitchSDK, arguments: dict) -> list[TextContent]:
    params = EndPredictionRequest(**arguments)
    result = await predictions.end_prediction(sdk.http, params)
    pred = result.data[0]
    return [TextContent(type="text", text=f"Prediction ended: {pred.title} (Status: {pred.status})")]


def get_handlers() -> dict:
    """Return handlers for predictions tools."""
    return {
        "twitch_create_prediction": _handle_create_prediction,
        "twitch_get_predictions": _handle_get_predictions,
        "twitch_end_prediction": _handle_end_prediction,
    }
