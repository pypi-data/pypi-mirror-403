"""EventSub WebSocket listener for real-time Twitch events."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from twitch_sdk import TwitchSDK
from twitch_sdk.endpoints.eventsub import EventSubWebSocket

from .handlers import default_handler, get_handler


class EventSubListener:
    """EventSub WebSocket listener that connects to Twitch and handles events.

    Features:
    - Connects to Twitch EventSub WebSocket
    - Subscribes to configured event types
    - Routes events to handlers
    - Optionally logs events to a file
    """

    def __init__(
        self,
        sdk: TwitchSDK,
        log_file: str | Path | None = None,
        handler: Callable[[dict], None] | None = None,
    ):
        """Initialize the EventSub listener.

        Args:
            sdk: TwitchSDK instance for API calls
            log_file: Optional path to log events (JSON lines format)
            handler: Optional custom event handler function
        """
        self.sdk = sdk
        self.log_file = Path(log_file) if log_file else None
        self.handler = handler or default_handler
        self._ws: EventSubWebSocket | None = None
        self._running = False

    async def connect(self) -> str:
        """Connect to EventSub WebSocket.

        Returns:
            Session ID for creating subscriptions.
        """
        self._ws = EventSubWebSocket(self.sdk.http)
        session_id = await self._ws.connect()
        print(f"[EventSub] Connected with session ID: {session_id}")
        return session_id

    async def subscribe(
        self,
        event_type: str,
        version: str,
        condition: dict,
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Event type (e.g., "channel.chat.message")
            version: Subscription version
            condition: Event condition (broadcaster_user_id, etc.)
        """
        if not self._ws:
            raise RuntimeError("Not connected. Call connect() first.")

        subscription = await self._ws.subscribe(event_type, version, condition)
        print(f"[EventSub] Subscribed to {event_type}: {subscription.status}")

    async def listen(self) -> None:
        """Start listening for events. Runs until stopped."""
        if not self._ws:
            raise RuntimeError("Not connected. Call connect() first.")

        self._running = True
        print("[EventSub] Listening for events... (Ctrl+C to stop)")

        try:
            async for event in self._ws.events():
                await self._handle_event(event)
        except asyncio.CancelledError:
            print("[EventSub] Listener stopped")
        finally:
            self._running = False

    async def _handle_event(self, event: dict) -> None:
        """Handle an incoming event.

        Args:
            event: Event payload from WebSocket
        """
        timestamp = datetime.utcnow().isoformat()

        # Log to file if configured
        if self.log_file:
            log_entry = {
                "timestamp": timestamp,
                "event": event,
            }
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        # Check for revocation
        if "revocation" in event:
            print(f"[EventSub] Subscription revoked: {event['revocation']}")
            return

        # Get subscription type
        subscription = event.get("subscription", {})
        event_type = subscription.get("type", "unknown")
        event_data = event.get("event", {})

        # Route to handler
        handler = get_handler(event_type) or self.handler

        try:
            # Handlers can be sync or async
            if asyncio.iscoroutinefunction(handler):
                await handler(event_type, event_data)
            else:
                handler(event_type, event_data)
        except Exception as e:
            print(f"[EventSub] Handler error for {event_type}: {e}")

    async def stop(self) -> None:
        """Stop the listener and close connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        print("[EventSub] Disconnected")

    async def __aenter__(self) -> "EventSubListener":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()


async def run_listener(
    subscriptions: list[dict] | None = None,
    log_file: str | None = None,
) -> None:
    """Run the EventSub listener with default subscriptions.

    Args:
        subscriptions: List of subscription configs, each with:
            - type: Event type (e.g., "channel.chat.message")
            - version: Subscription version
            - condition: Event condition dict
        log_file: Optional path to log events
    """
    # Load .env file if TWITCH_ENV_FILE is set
    env_file = os.getenv("TWITCH_ENV_FILE")
    if env_file and Path(env_file).exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    # Initialize SDK
    sdk = TwitchSDK()

    # Get broadcaster ID from environment or SDK
    broadcaster_id = os.getenv("TWITCH_BROADCASTER_ID")
    user_id = os.getenv("TWITCH_USER_ID")

    # Default subscriptions if none provided
    if not subscriptions:
        if not broadcaster_id:
            print("[EventSub] No TWITCH_BROADCASTER_ID set, skipping default subscriptions")
            subscriptions = []
        else:
            subscriptions = [
                {
                    "type": "channel.chat.message",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": broadcaster_id,
                        "user_id": user_id or broadcaster_id,
                    },
                },
                {
                    "type": "channel.follow",
                    "version": "2",
                    "condition": {
                        "broadcaster_user_id": broadcaster_id,
                        "moderator_user_id": user_id or broadcaster_id,
                    },
                },
                {
                    "type": "channel.subscribe",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": broadcaster_id,
                    },
                },
                {
                    "type": "channel.raid",
                    "version": "1",
                    "condition": {
                        "to_broadcaster_user_id": broadcaster_id,
                    },
                },
            ]

    try:
        async with EventSubListener(sdk, log_file=log_file) as listener:
            # Subscribe to events
            for sub in subscriptions:
                try:
                    await listener.subscribe(
                        sub["type"],
                        sub["version"],
                        sub["condition"],
                    )
                except Exception as e:
                    print(f"[EventSub] Failed to subscribe to {sub['type']}: {e}")

            # Listen for events
            await listener.listen()

    finally:
        await sdk.close()


def main():
    """CLI entry point for eventsub-listen command."""
    import argparse

    parser = argparse.ArgumentParser(description="EventSub WebSocket listener")
    parser.add_argument(
        "--log",
        "-l",
        help="Path to log events (JSON lines format)",
    )
    parser.add_argument(
        "--broadcaster",
        "-b",
        help="Broadcaster user ID (overrides TWITCH_BROADCASTER_ID)",
    )
    args = parser.parse_args()

    # Override env vars if provided
    if args.broadcaster:
        os.environ["TWITCH_BROADCASTER_ID"] = args.broadcaster

    try:
        asyncio.run(run_listener(log_file=args.log))
    except KeyboardInterrupt:
        print("\n[EventSub] Shutting down...")


if __name__ == "__main__":
    main()
