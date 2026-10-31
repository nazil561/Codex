import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.config import settings
from live_engagement_coach.db.models import TwitchAccount
from live_engagement_coach.security.crypto import decrypt_token, encrypt_token
from live_engagement_coach.twitch.oauth import TwitchOAuth


class HelixClient:
    BASE = "https://api.twitch.tv/helix"

    def __init__(self, account: TwitchAccount, session: AsyncSession):
        self.account = account
        self.session = session
        self._lock = asyncio.Lock()

    async def _get_headers(self) -> dict[str, str]:
        access = decrypt_token(self.account.access_token_ciphertext)
        return {"Authorization": f"Bearer {access}", "Client-Id": settings.TWITCH_CLIENT_ID}

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with self._lock:
            headers = await self._get_headers()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.request(method, url, headers=headers, **kwargs)
                if resp.status_code == 401:
                    try:
                        refresh = decrypt_token(self.account.refresh_token_ciphertext)
                        tr = await TwitchOAuth.refresh_token(refresh)
                        new_access = tr["access_token"]
                        new_refresh = tr.get("refresh_token") or refresh
                        self.account.access_token_ciphertext = encrypt_token(new_access)
                        self.account.refresh_token_ciphertext = encrypt_token(new_refresh)
                        from datetime import timedelta
                        expires_in = tr.get("expires_in")
                        if expires_in:
                            self.account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                        self.account.status = "connected"
                        await self.session.commit()
                        headers = {"Authorization": f"Bearer {new_access}", "Client-Id": settings.TWITCH_CLIENT_ID}
                        resp = await client.request(method, url, headers=headers, **kwargs)
                    except Exception:
                        self.account.status = "needs_reauth"
                        await self.session.commit()
                        try:
                            from live_engagement_coach import state
                            await state.listener_manager.stop_listener(self.account.id)
                        except Exception:
                            pass
                        raise
                if resp.status_code == 429:
                    raise httpx.HTTPStatusError("rate_limited", request=resp.request, response=resp)
                resp.raise_for_status()
                return resp

    async def get_users(self, user_id: str | None = None, login: str | None = None) -> dict:
        params = {}
        if user_id:
            params["id"] = user_id
        if login:
            params["login"] = login
        resp = await self._request("GET", f"{self.BASE}/users", params=params)
        return resp.json()

    async def get_streams(self, user_id: str) -> dict:
        resp = await self._request("GET", f"{self.BASE}/streams", params={"user_id": user_id})
        return resp.json()

    async def get_polls(self, broadcaster_id: str, poll_id: str | None = None) -> dict:
        params = {"broadcaster_id": broadcaster_id}
        if poll_id:
            params["id"] = poll_id
        resp = await self._request("GET", f"{self.BASE}/polls", params=params)
        return resp.json()

    async def validate(self) -> dict:
        access = decrypt_token(self.account.access_token_ciphertext)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"OAuth {access}"})
            if resp.status_code != 200:
                raise httpx.HTTPStatusError("invalid", request=resp.request, response=resp)
            return resp.json()
