from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.api.deps import get_current_account
from live_engagement_coach.db.models import TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach.services.stream import get_stream_fresh

router = APIRouter()


@router.get("/stream")
async def stream(acc: TwitchAccount = Depends(get_current_account), session: AsyncSession = Depends(get_session)):
    try:
        return await get_stream_fresh(session, acc)
    except Exception:
        raise HTTPException(status_code=503, detail={"error": {"code": "twitch_unavailable", "message": "Twitch unavailable"}})
