from datetime import datetime, timezone


def parse_chat_message(event: dict) -> dict | None:
    # event structure per Twitch
    message_id = event.get("message_id") or event.get("id")
    broadcaster_user_id = event.get("broadcaster_user_id")
    chatter_user_id = event.get("chatter_user_id") or event.get("user_id")
    message_timestamp = event.get("message_timestamp") or event.get("timestamp") or datetime.now(timezone.utc).isoformat()
    try:
        ts = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
    except Exception:
        ts = datetime.now(timezone.utc)
    if not message_id:
        return None
    return {
        "message_id": message_id,
        "broadcaster_user_id": broadcaster_user_id,
        "chatter_user_id": chatter_user_id,
        "timestamp": ts,
        "bucket_start": ts.replace(second=0, microsecond=0),
    }
