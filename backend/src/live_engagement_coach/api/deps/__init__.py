from typing import Any

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.db.models import AppSession, TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach.security.sessions import hash_session_token


async def get_current_account(
    lec_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> TwitchAccount:
    if not lec_session:
        raise HTTPException(status_code=401, detail={"error": {"code": "unauthenticated", "message": "Unauthenticated"}})
    token_hash = hash_session_token(lec_session)
    res = await session.execute(select(AppSession).where(AppSession.token_hash == token_hash))
    app_s = res.scalar_one_or_none()
    if not app_s:
        raise HTTPException(status_code=401, detail={"error": {"code": "unauthenticated", "message": "Unauthenticated"}})
    res = await session.execute(select(TwitchAccount).where(TwitchAccount.id == app_s.twitch_account_id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=401, detail={"error": {"code": "unauthenticated", "message": "Unauthenticated"}})
    return acc
