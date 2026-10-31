from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.config import settings
from live_engagement_coach.db.models import Poll, PollChoice, StreamSnapshot, Suggestion, TwitchAccount
from live_engagement_coach.security.crypto import decrypt_token
from live_engagement_coach.services.stream import get_stream_fresh


class PollService:
    def __init__(self, session: AsyncSession, acc: TwitchAccount):
        self.session = session
        self.acc = acc

    async def approve_suggestion(self, suggestion_id: str):
        try:
            sid = UUID(suggestion_id)
        except Exception:
            raise HTTPException(status_code=409, detail={"error": {"code": "suggestion_not_pending", "message": "Not pending"}})
        res = await self.session.execute(select(Suggestion).where(Suggestion.id == sid, Suggestion.twitch_account_id == self.acc.id))
        s = res.scalar_one_or_none()
        if not s or s.status != "proposed":
            raise HTTPException(status_code=409, detail={"error": {"code": "suggestion_not_pending", "message": "Not pending"}})
        try:
            sf = await get_stream_fresh(self.session, self.acc)
            if not sf.get("is_live"):
                raise HTTPException(status_code=409, detail={"error": {"code": "stream_offline", "message": "Stream offline"}})
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=409, detail={"error": {"code": "stream_offline", "message": "Stream offline"}})
        action = s.action_payload
        payload = {
            "broadcaster_id": self.acc.twitch_user_id,
            "title": str(action.get("title", ""))[:60],
            "choices": [{"title": str(c)[:25]} for c in action.get("choices", [])],
            "duration": int(action.get("duration_seconds", 60)),
        }
        access = decrypt_token(self.acc.access_token_ciphertext)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.twitch.tv/helix/polls",
                json=payload,
                headers={"Authorization": f"Bearer {access}", "Client-Id": settings.TWITCH_CLIENT_ID},
            )
            if resp.status_code == 400:
                try:
                    body = resp.json()
                except Exception:
                    body = {}
                if "already" in str(body).lower():
                    raise HTTPException(status_code=409, detail={"error": {"code": "poll_already_active", "message": "A poll is already running on this channel."}})
                raise HTTPException(status_code=400, detail={"error": {"code": "bad_request", "message": "Bad request"}})
            if resp.status_code == 401:
                raise HTTPException(status_code=401, detail={"error": {"code": "needs_reauth", "message": "Reauth required"}})
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail={"error": {"code": "twitch_poll_failed", "message": "Poll failed"}})
            data = resp.json()
            pd = data.get("data", [{}])[0]
            poll = Poll(
                twitch_account_id=self.acc.id,
                suggestion_id=s.id,
                twitch_poll_id=pd["id"],
                title=pd["title"],
                duration_seconds=payload["duration"],
                twitch_status=pd.get("status", "ACTIVE"),
                started_at=datetime.now(timezone.utc),
            )
            self.session.add(poll)
            await self.session.flush()
            for c in pd.get("choices", []):
                self.session.add(PollChoice(poll_id=poll.id, twitch_choice_id=c["id"], title=c["title"], votes=c.get("votes", 0), channel_points_votes=c.get("channel_points_votes", 0)))
            s.status = "executed"
            s.decided_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(poll)
            rc = await self.session.execute(select(PollChoice).where(PollChoice.poll_id == poll.id))
            choices = [{"id": str(ch.id), "title": ch.title, "votes": ch.votes, "channel_points_votes": ch.channel_points_votes} for ch in rc.scalars()]
            return {
                "id": str(poll.id),
                "suggestion_id": str(s.id),
                "twitch_poll_id": poll.twitch_poll_id,
                "title": poll.title,
                "status": "active",
                "twitch_status": poll.twitch_status,
                "duration_seconds": poll.duration_seconds,
                "started_at": poll.started_at.isoformat().replace("+00:00", "Z"),
                "ended_at": None,
                "freshness": "live",
                "choices": choices,
            }
