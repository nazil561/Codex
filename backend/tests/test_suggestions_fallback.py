def test_suggestions_fallback():
    from live_engagement_coach.services.rules import build_rules_suggestion
    m = {"window_minutes": 15, "chat_messages": 4, "unique_chatters": 2, "latest_viewer_count": 18, "chat_participation_ratio": 0.11, "is_live": True}
    r = build_rules_suggestion(m)
    assert r["source"] == "rules"
    assert "create_poll" == r["action"]["type"]
    assert len(r["action"]["choices"]) >= 2
