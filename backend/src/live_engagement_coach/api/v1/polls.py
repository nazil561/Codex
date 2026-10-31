from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.api.deps import get_current_account
from live_engagement_coach.db.models import Poll, PollChoice, TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach.twitch.client import HelixClient

router = APIRouter()


@router.get("/polls")
async def list_polls(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Poll).where(Poll.twitch_account_id == acc.id))
    out = []
    for p in res.scalars():
        rc = await session.execute(select(PollChoice).where(PollChoice.poll_id == p.id))
        choices = [{"id": str(c.id), "title": c.title, "votes": c.votes, "channel_points_votes": c.channel_points_votes} for c in rc.scalars()]
        out.append({
            "id": str(p.id),
            "suggestion_id": str(p.suggestion_id),
            "twitch_poll_id": p.twitch_poll_id,
            "title": p.title,
            "status": "active" if p.twitch_status == "ACTIVE" else p.twitch_status.lower(),
            "twitch_status": p.twitch_status,
            "duration_seconds": p.duration_seconds,
            "started_at": p.started_at.isoformat().replace("+00:00", "Z"),
            "ended_at": p.ended_at.isoformat().replace("+00:00", "Z") if p.ended_at else None,
            "freshness": "live",
            "choices": choices,
        })
    return {"polls": out}


@router.get("/polls/{poll_id}")
async def get_poll(poll_id: str, acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    from uuid import UUID

    try:
        pid = UUID(poll_id)
    except Exception:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Not found"}})
    res = await session.execute(select(Poll).where(Poll.id == pid, Poll.twitch_account_id == acc.id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Not found"}})
    # refresh if active
    if p.twitch_status == "ACTIVE":
        try:
            hc = HelixClient(acc, session)
            data = await hc.get_polls(acc.twitch_user_id, p.twitch_poll_id)
            pdlist = data.get("data", [])
            if pdlist:
                pd = pdlist[0]
                p.twitch_status = pd.get("status", p.twitch_status)
                if pd.get("ended_at"):
                    try:
                        p.ended_at = datetime.fromisoformat(pd["ended_at"].replace("Z", "+00:00"))
                    except Exception:
                        pass
                # update choices
                for c in pd.get("choices", []):
                    rc2 = await session.execute(select(PollChoice).where(PollChoice.poll_id == p.id, PollChoice.twitch_choice_id == c["id"]))
                    pc = rc2.scalar_one_or_none()
                    if pc:
                        pc.votes = c.get("votes", pc.votes)
                        pc.channel_points_votes = c.get("channel_points_votes", pc.channel_points_votes)
                await session.commit()
                await session.refresh(p)
        except Exception:
            pass
    rc = await session.execute(select(PollChoice).where(PollChoice.poll_id == p.id))
    choices = [{"id": str(c.id), "title": c.title, "votes": c.votes, "channel_points_votes": c.channel_points_votes} for c in rc.scalars()]
    return {
        "id": str(p.id),
        "suggestion_id": str(p.suggestion_id),
        "twitch_poll_id": p.twitch_poll_id,
        "title": p.title,
        "status": "active" if p.twitch_status == "ACTIVE" else p.twitch_status.lower(),
        "twitch_status": p.twitch_status,
        "duration_seconds": p.duration_seconds,
        "started_at": p.started_at.isoformat().replace("+00:00", "Z"),
        "ended_at": p.ended_at.isoformat().replace("+00:00", "Z") if p.ended_at else None,
        "freshness": "live" if p.twitch_status == "ACTIVE" else "live",
        "choices": choices,
    }
