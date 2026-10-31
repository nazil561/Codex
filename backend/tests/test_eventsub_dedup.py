from datetime import datetime, timezone

from live_engagement_coach.db import models


def test_eventsub_dedup():
    from live_engagement_coach.twitch.parsers import parse_chat_message
    ev = {"message_id": "m1", "broadcaster_user_id": "1", "chatter_user_id": "2", "message_timestamp": "2026-10-28T01:40:00Z"}
    p = parse_chat_message(ev)
    assert p["bucket_start"].minute == 40
