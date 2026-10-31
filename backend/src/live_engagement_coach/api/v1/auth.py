from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.api.deps import get_current_account
from live_engagement_coach.config import settings
from live_engagement_coach.db.models import AppSession, OAuthState, TwitchAccount
from live_engagement_coach.db.session import get_session
from live_engagement_coach.security.crypto import encrypt_token
from live_engagement_coach.security.sessions import generate_state, hash_session_token, hash_state
from live_engagement_coach.twitch.oauth import TwitchOAuth

router = APIRouter()

SCOPES = ["user:read:chat", "channel:manage:polls", "channel:read:polls"]


@router.get("/auth/twitch/start")
async def twitch_start(session: AsyncSession = Depends(get_session)):
    state = generate_state()
    st = OAuthState(state_hash=hash_state(state), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
    session.add(st)
    await session.commit()
    url = TwitchOAuth.build_auth_url(state, SCOPES)
    return RedirectResponse(url=url, status_code=302)


@router.get("/auth/twitch/callback")
async def twitch_callback(request: Request, session: AsyncSession = Depends(get_session)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    if error == "access_denied":
        return RedirectResponse(url=settings.FRONTEND_SUCCESS_URL + "?error=access_denied", status_code=302)
    if not code or not state:
        return RedirectResponse(url=settings.FRONTEND_SUCCESS_URL + "?error=invalid_oauth_state", status_code=302)
    sh = hash_state(state)
    res = await session.execute(select(OAuthState).where(OAuthState.state_hash == sh))
    ost = res.scalar_one_or_none()
    if not ost or ost.consumed_at is not None or ost.expires_at < datetime.now(timezone.utc):
        return RedirectResponse(url=settings.FRONTEND_SUCCESS_URL + "?error=invalid_oauth_state", status_code=302)
    ost.consumed_at = datetime.now(timezone.utc)
    await session.commit()
    try:
        token_resp = await TwitchOAuth.exchange_code(code)
    except Exception:
        return RedirectResponse(url=settings.FRONTEND_SUCCESS_URL + "?error=token_exchange_failed", status_code=302)

    access_token = token_resp["access_token"]
    refresh_token = token_resp.get("refresh_token", "")
    expires_in = token_resp.get("expires_in")
    scopes = token_resp.get("scope") or SCOPES

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/users",
            headers={"Authorization": f"Bearer {access_token}", "Client-Id": settings.TWITCH_CLIENT_ID},
        )
        resp.raise_for_status()
        user = resp.json()["data"][0]

    twitch_user_id = user["id"]
    res = await session.execute(select(TwitchAccount).where(TwitchAccount.twitch_user_id == twitch_user_id))
    acc = res.scalar_one_or_none()
    if not acc:
        acc = TwitchAccount(
            twitch_user_id=twitch_user_id,
            login=user["login"],
            display_name=user["display_name"],
            access_token_ciphertext=encrypt_token(access_token),
            refresh_token_ciphertext=encrypt_token(refresh_token),
            token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None,
            scopes=scopes,
            status="connected",
        )
        session.add(acc)
        await session.flush()
    else:
        acc.login = user["login"]
        acc.display_name = user["display_name"]
        acc.access_token_ciphertext = encrypt_token(access_token)
        acc.refresh_token_ciphertext = encrypt_token(refresh_token)
        acc.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None
        acc.scopes = scopes
        acc.status = "connected"
        await session.flush()

    raw = uuid4().hex + uuid4().hex
    app_s = AppSession(twitch_account_id=acc.id, token_hash=hash_session_token(raw), expires_at=datetime.now(timezone.utc) + timedelta(hours=12))
    session.add(app_s)
    await session.commit()

    resp = RedirectResponse(url=settings.FRONTEND_SUCCESS_URL, status_code=302)
    resp.set_cookie("lec_session", raw, httponly=True, samesite="lax", secure=settings.PUBLIC_BASE_URL.startswith("https"), path="/")
    return resp


@router.post("/auth/logout")
async def logout(session: AsyncSession = Depends(get_session), acc: TwitchAccount = Depends(get_current_account)):
    from sqlalchemy import delete
    from live_engagement_coach.db.models import AppSession

    await session.execute(delete(AppSession).where(AppSession.twitch_account_id == acc.id))
    await session.commit()
    resp = JSONResponse(status_code=204, content=None)
    resp.delete_cookie("lec_session", path="/")
    return resp


@router.get("/me")
async def me(acc: TwitchAccount = Depends(get_current_account)):
    return {"twitch_user_id": acc.twitch_user_id, "login": acc.login, "display_name": acc.display_name, "scopes": acc.scopes, "status": acc.status}
