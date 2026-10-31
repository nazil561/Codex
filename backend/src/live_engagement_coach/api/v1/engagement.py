from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.api.deps import get_current_account
from live_engagement_coach.db.models import ListeningSession, TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach import state

router = APIRouter()


@router.get("/engagement/session")
async def session_get(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(ListeningSession).where(ListeningSession.twitch_account_id == acc.id).order_by(desc(ListeningSession.started_at)).limit(1))
    ls = res.scalar_one_or_none()
    if not ls:
        return {"status": "stopped", "subscriptions": [], "last_gap_at": None, "last_event_at": None}
    return {
        "status": ls.status,
        "subscriptions": ["channel.chat.message", "channel.poll.begin", "channel.poll.progress", "channel.poll.end"] if ls.status in ("listening", "degraded") else [],
        "last_gap_at": ls.last_gap_at.isoformat().replace("+00:00", "Z") if ls.last_gap_at else None,
        "last_event_at": ls.last_event_at.isoformat().replace("+00:00", "Z") if ls.last_event_at else None,
    }


@router.post("/engagement/session/start")
async def session_start(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    required = {"user:read:chat", "channel:manage:polls", "channel:read:polls"}
    if not required.issubset(set(acc.scopes or [])):
        raise HTTPException(status_code=403, detail={"error": {"code": "missing_scope", "message": "Missing scope"}})
    await state.listener_manager.start_listener(acc.id)
    return {"status": "listening", "subscriptions": ["channel.chat.message", "channel.poll.begin", "channel.poll.progress", "channel.poll.end"], "last_gap_at": None}


@router.post("/engagement/session/stop")
async def session_stop(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    await state.listener_manager.stop_listener(acc.id)
    return {"status": "stopped"}


@router.get("/metrics")
async def metrics(window_minutes: int = 15, acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    try:
        from live_engagement_coach.services.metrics import get_metrics

        return await get_metrics(session, acc, window_minutes)
    except HTTPException:
        raise
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail={"error": {"code": "invalid_window", "message": "Invalid window"}})
