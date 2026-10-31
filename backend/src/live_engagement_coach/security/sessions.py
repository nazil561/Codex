import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from live_engagement_coach.config import settings


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def hash_state(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def hash_session_token(token: str) -> str:
    pepper = settings.SESSION_PEPPER or "dev-pepper"
    return hmac.new(pepper.encode(), token.encode(), hashlib.sha256).hexdigest()


def hash_chatter_id(chatter_id: str) -> str:
    pepper = settings.CHATTER_HASH_PEPPER or "dev-chatter-pepper"
    return hmac.new(pepper.encode(), chatter_id.encode(), hashlib.sha256).hexdigest()
