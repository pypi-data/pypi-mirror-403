"""Event handlers for EventSub events."""

from typing import Callable

# Registry of event handlers
_handlers: dict[str, Callable] = {}


def register_handler(event_type: str):
    """Decorator to register an event handler.

    Usage:
        @register_handler("channel.chat.message")
        def handle_chat_message(event_type: str, data: dict):
            print(f"Chat: {data['chatter_user_name']}: {data['message']['text']}")
    """
    def decorator(func: Callable):
        _handlers[event_type] = func
        return func
    return decorator


def get_handler(event_type: str) -> Callable | None:
    """Get the registered handler for an event type."""
    return _handlers.get(event_type)


def default_handler(event_type: str, data: dict) -> None:
    """Default handler that prints events to console."""
    print(f"[Event] {event_type}: {data}")


# Built-in handlers for common events

@register_handler("channel.chat.message")
def handle_chat_message(event_type: str, data: dict) -> None:
    """Handle chat messages."""
    chatter = data.get("chatter_user_name", "Unknown")
    message = data.get("message", {}).get("text", "")
    badges = data.get("badges", [])

    # Format badges
    badge_str = ""
    for badge in badges:
        badge_id = badge.get("set_id", "")
        if badge_id == "broadcaster":
            badge_str += "[STREAMER] "
        elif badge_id == "moderator":
            badge_str += "[MOD] "
        elif badge_id == "vip":
            badge_str += "[VIP] "
        elif badge_id == "subscriber":
            badge_str += "[SUB] "

    print(f"[Chat] {badge_str}{chatter}: {message}")


@register_handler("channel.follow")
def handle_follow(event_type: str, data: dict) -> None:
    """Handle new followers."""
    follower = data.get("user_name", "Unknown")
    broadcaster = data.get("broadcaster_user_name", "Unknown")
    print(f"[Follow] {follower} followed {broadcaster}!")


@register_handler("channel.subscribe")
def handle_subscribe(event_type: str, data: dict) -> None:
    """Handle new subscriptions."""
    subscriber = data.get("user_name", "Unknown")
    tier = data.get("tier", "1000")
    is_gift = data.get("is_gift", False)

    tier_name = {"1000": "Tier 1", "2000": "Tier 2", "3000": "Tier 3"}.get(tier, tier)

    if is_gift:
        print(f"[Sub] {subscriber} received a gifted {tier_name} subscription!")
    else:
        print(f"[Sub] {subscriber} subscribed at {tier_name}!")


@register_handler("channel.subscription.gift")
def handle_gift_sub(event_type: str, data: dict) -> None:
    """Handle gift subscriptions."""
    gifter = data.get("user_name", "Anonymous")
    total = data.get("total", 1)
    tier = data.get("tier", "1000")
    tier_name = {"1000": "Tier 1", "2000": "Tier 2", "3000": "Tier 3"}.get(tier, tier)
    print(f"[Gift] {gifter} gifted {total} {tier_name} sub(s)!")


@register_handler("channel.subscription.message")
def handle_resub_message(event_type: str, data: dict) -> None:
    """Handle resubscription messages."""
    subscriber = data.get("user_name", "Unknown")
    months = data.get("cumulative_months", 1)
    message = data.get("message", {}).get("text", "")
    tier = data.get("tier", "1000")
    tier_name = {"1000": "Tier 1", "2000": "Tier 2", "3000": "Tier 3"}.get(tier, tier)
    print(f"[Resub] {subscriber} resubscribed for {months} months at {tier_name}!")
    if message:
        print(f"  Message: {message}")


@register_handler("channel.cheer")
def handle_cheer(event_type: str, data: dict) -> None:
    """Handle bits cheers."""
    cheerer = data.get("user_name", "Anonymous")
    bits = data.get("bits", 0)
    message = data.get("message", "")
    print(f"[Bits] {cheerer} cheered {bits} bits!")
    if message:
        print(f"  Message: {message}")


@register_handler("channel.raid")
def handle_raid(event_type: str, data: dict) -> None:
    """Handle incoming raids."""
    raider = data.get("from_broadcaster_user_name", "Unknown")
    viewers = data.get("viewers", 0)
    print(f"[Raid] {raider} raided with {viewers} viewers!")


@register_handler("channel.poll.begin")
def handle_poll_begin(event_type: str, data: dict) -> None:
    """Handle poll start."""
    title = data.get("title", "Poll")
    choices = data.get("choices", [])
    choice_list = ", ".join([c.get("title", "") for c in choices])
    print(f"[Poll] Started: {title}")
    print(f"  Choices: {choice_list}")


@register_handler("channel.poll.end")
def handle_poll_end(event_type: str, data: dict) -> None:
    """Handle poll end."""
    title = data.get("title", "Poll")
    status = data.get("status", "completed")
    choices = data.get("choices", [])

    # Find winner
    winner = max(choices, key=lambda c: c.get("votes", 0)) if choices else {}
    print(f"[Poll] Ended ({status}): {title}")
    if winner:
        print(f"  Winner: {winner.get('title')} with {winner.get('votes', 0)} votes")


@register_handler("channel.prediction.begin")
def handle_prediction_begin(event_type: str, data: dict) -> None:
    """Handle prediction start."""
    title = data.get("title", "Prediction")
    outcomes = data.get("outcomes", [])
    outcome_list = ", ".join([o.get("title", "") for o in outcomes])
    print(f"[Prediction] Started: {title}")
    print(f"  Outcomes: {outcome_list}")


@register_handler("channel.prediction.end")
def handle_prediction_end(event_type: str, data: dict) -> None:
    """Handle prediction end."""
    title = data.get("title", "Prediction")
    status = data.get("status", "resolved")
    winning_outcome = data.get("winning_outcome_id")
    outcomes = data.get("outcomes", [])

    print(f"[Prediction] Ended ({status}): {title}")
    if winning_outcome:
        winner = next((o for o in outcomes if o.get("id") == winning_outcome), {})
        print(f"  Winner: {winner.get('title', 'Unknown')}")


@register_handler("channel.hype_train.begin")
def handle_hype_train_begin(event_type: str, data: dict) -> None:
    """Handle hype train start."""
    level = data.get("level", 1)
    print(f"[Hype Train] Started at level {level}!")


@register_handler("channel.hype_train.progress")
def handle_hype_train_progress(event_type: str, data: dict) -> None:
    """Handle hype train progress."""
    level = data.get("level", 1)
    progress = data.get("progress", 0)
    goal = data.get("goal", 100)
    print(f"[Hype Train] Level {level}: {progress}/{goal}")


@register_handler("channel.hype_train.end")
def handle_hype_train_end(event_type: str, data: dict) -> None:
    """Handle hype train end."""
    level = data.get("level", 1)
    print(f"[Hype Train] Ended at level {level}!")


@register_handler("stream.online")
def handle_stream_online(event_type: str, data: dict) -> None:
    """Handle stream going live."""
    broadcaster = data.get("broadcaster_user_name", "Unknown")
    stream_type = data.get("type", "live")
    print(f"[Stream] {broadcaster} went {stream_type}!")


@register_handler("stream.offline")
def handle_stream_offline(event_type: str, data: dict) -> None:
    """Handle stream going offline."""
    broadcaster = data.get("broadcaster_user_name", "Unknown")
    print(f"[Stream] {broadcaster} went offline!")


@register_handler("channel.ban")
def handle_ban(event_type: str, data: dict) -> None:
    """Handle user bans."""
    banned = data.get("user_name", "Unknown")
    moderator = data.get("moderator_user_name", "Unknown")
    reason = data.get("reason", "No reason provided")
    is_permanent = data.get("is_permanent", True)

    if is_permanent:
        print(f"[Ban] {banned} was permanently banned by {moderator}")
    else:
        ends_at = data.get("ends_at", "unknown time")
        print(f"[Timeout] {banned} was timed out by {moderator} until {ends_at}")
    print(f"  Reason: {reason}")


@register_handler("channel.unban")
def handle_unban(event_type: str, data: dict) -> None:
    """Handle user unbans."""
    unbanned = data.get("user_name", "Unknown")
    moderator = data.get("moderator_user_name", "Unknown")
    print(f"[Unban] {unbanned} was unbanned by {moderator}")


@register_handler("channel.moderator.add")
def handle_mod_add(event_type: str, data: dict) -> None:
    """Handle new moderators."""
    new_mod = data.get("user_name", "Unknown")
    print(f"[Mod] {new_mod} was made a moderator!")


@register_handler("channel.moderator.remove")
def handle_mod_remove(event_type: str, data: dict) -> None:
    """Handle moderator removals."""
    former_mod = data.get("user_name", "Unknown")
    print(f"[Mod] {former_mod} is no longer a moderator")
