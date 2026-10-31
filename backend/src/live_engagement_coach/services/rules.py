def build_rules_suggestion(metrics: dict) -> dict:
    is_live = metrics.get("is_live")
    cm = metrics.get("chat_messages", 0)
    uc = metrics.get("unique_chatters", 0)
    lvc = metrics.get("latest_viewer_count")
    ratio = metrics.get("chat_participation_ratio")
    if is_live and cm < 10:
        title = "What should we do next?"
        choices = ["Boss fight", "Viewer challenge"]
    else:
        title = "Quick poll"
        choices = ["Yes", "No"]
    rationale = f"In the last {metrics.get('window_minutes')} minutes there were {cm} chat messages from {uc} unique chatters while the latest viewer sample was {lvc}. A one-minute poll gives people a way to participate without typing."
    return {
        "source": "rules",
        "rationale": rationale,
        "action": {"type": "create_poll", "title": title, "choices": choices, "duration_seconds": 60},
    }
