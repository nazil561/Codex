from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.api.deps import get_current_account
from live_engagement_coach.db.models import Suggestion, TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach.services.suggestions import SuggestionService
from live_engagement_coach.services.polls import PollService

router = APIRouter()


@router.post("/suggestions", status_code=201)
async def create_suggestion(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    svc = SuggestionService(session, acc)
    return await svc.create_suggestion()


@router.get("/suggestions")
async def list_suggestions(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Suggestion).where(Suggestion.twitch_account_id == acc.id))
    out = []
    for s in res.scalars():
        out.append(
            {
                "id": str(s.id),
                "status": s.status,
                "source": s.source,
                "rationale": s.rationale,
                "evidence": s.evidence,
                "action": s.action_payload,
                "created_at": s.created_at.isoformat().replace("+00:00", "Z"),
            }
        )
    return out


@router.get("/suggestions/{suggestion_id}")
async def get_suggestion(suggestion_id: str, acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    from uuid import UUID

    try:
        sid = UUID(suggestion_id)
    except Exception:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Not found"}})
    res = await session.execute(select(Suggestion).where(Suggestion.id == sid, Suggestion.twitch_account_id == acc.id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Not found"}})
    return {
        "id": str(s.id),
        "status": s.status,
        "source": s.source,
        "rationale": s.rationale,
        "evidence": s.evidence,
        "action": s.action_payload,
        "created_at": s.created_at.isoformat().replace("+00:00", "Z"),
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: str, acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    from uuid import UUID
    from datetime import datetime, timezone

    try:
        sid = UUID(suggestion_id)
    except Exception:
        raise HTTPException(status_code=409, detail={"error": {"code": "suggestion_not_pending", "message": "Not pending"}})
    res = await session.execute(select(Suggestion).where(Suggestion.id == sid, Suggestion.twitch_account_id == acc.id))
    s = res.scalar_one_or_none()
    if not s or s.status != "proposed":
        raise HTTPException(status_code=409, detail={"error": {"code": "suggestion_not_pending", "message": "Not pending"}})
    s.status = "rejected"
    s.decided_at = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "rejected"}


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: str, acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    svc = PollService(session, acc)
    return await svc.approve_suggestion(suggestion_id)
