from urllib.parse import urlencode

import httpx

from live_engagement_coach.config import settings


class TwitchOAuth:
    AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"

    @staticmethod
    def build_auth_url(state: str, scopes: list[str]) -> str:
        params = {
            "response_type": "code",
            "client_id": settings.TWITCH_CLIENT_ID,
            "redirect_uri": settings.TWITCH_REDIRECT_URI,
            "scope": " ".join(scopes),
            "state": state,
        }
        return f"{TwitchOAuth.AUTH_URL}?{urlencode(params)}"

    @staticmethod
    async def exchange_code(code: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                TwitchOAuth.TOKEN_URL,
                data={
                    "client_id": settings.TWITCH_CLIENT_ID,
                    "client_secret": settings.TWITCH_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.TWITCH_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def refresh_token(refresh_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                TwitchOAuth.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.TWITCH_CLIENT_ID,
                    "client_secret": settings.TWITCH_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()
