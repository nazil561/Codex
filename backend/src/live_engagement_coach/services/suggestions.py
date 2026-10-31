import json
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.config import settings
from live_engagement_coach.db.models import Suggestion, TwitchAccount
from live_engagement_coach.services.metrics import get_metrics
from live_engagement_coach.services.rules import build_rules_suggestion


class SuggestionService:
    def __init__(self, session: AsyncSession, acc: TwitchAccount):
        self.session = session
        self.acc = acc

    async def create_suggestion(self):
        m = await get_metrics(self.session, self.acc, 15)
        evidence = {
            "window_minutes": m["window_minutes"],
            "chat_messages": m["chat_messages"],
            "unique_chatters": m["unique_chatters"],
            "latest_viewer_count": m["latest_viewer_count"],
            "chat_participation_ratio": m["chat_participation_ratio"],
            "is_live": m["is_live"],
        }
        source = "openai"
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_MODEL:
                # Enhanced prompt with persona and strict constraints
                prompt = (
                    f"You are a Twitch Stream Engagement Expert. Create a poll suggestion based on these metrics: {json.dumps(evidence)}. "
                    f"Constraints: 1. Use a friendly, encouraging tone for the streamer. "
                    f"2. NEVER use technical terms like 'retention', 'churn', or 'participation ratio' in the rationale. "
                    f"3. DO NOT mention specific chatter IDs or usernames. "
                    f"4. Keep it simple and actionable. "
                    f"Return JSON with: title (max 60), choices (2-5, each max 25), duration_seconds (15-1800), rationale."
                )
                async with httpx.AsyncClient(timeout=settings.OPENAI_TIMEOUT_SECONDS) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": settings.OPENAI_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant that suggests engaging polls for Twitch streamers based on chat metrics."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "response_format": {"type": "json_object"},
                        },
                    )
                    if resp.status_code != 200:
                        raise Exception(f"openai_failed_{resp.status_code}")
                    content = resp.json()["choices"][0]["message"]["content"]
                    data = json.loads(content)
                    action = {
                        "type": "create_poll",
                        "title": data["title"][:60],
                        "choices": data["choices"][:5],
                        "duration_seconds": int(data.get("duration_seconds", 60)),
                    }
                    rationale = data.get("rationale", "")
                if len(action["title"]) > 60 or len(action["choices"]) < 2 or len(action["choices"]) > 5 or any(len(c) > 25 for c in action["choices"]):
                    raise Exception("bad_schema")
            else:
                raise Exception("no_key")
        except Exception as e:
            import logging
            logging.getLogger("suggestions").warning(f"AI suggestion failed ({e}), falling back to rules.")
            r = build_rules_suggestion(m)
            source = "rules"
            action = r["action"]
            rationale = r["rationale"]
        s = Suggestion(
            twitch_account_id=self.acc.id,
            status="proposed",
            source=source,
            rationale=rationale,
            evidence=evidence,
            action_payload=action,
        )
        self.session.add(s)
        await self.session.commit()
        await self.session.refresh(s)
        return {
            "id": str(s.id),
            "status": s.status,
            "source": s.source,
            "rationale": s.rationale,
            "evidence": s.evidence,
            "action": s.action_payload,
            "created_at": s.created_at.isoformat().replace("+00:00", "Z"),
        }
