import base64
import os

from cryptography.fernet import Fernet

from live_engagement_coach.config import settings


def get_fernet() -> Fernet:
    key = settings.TOKEN_ENCRYPTION_KEY
    if not key:
        # dev fallback - not for production
        key = Fernet.generate_key().decode()
    # ensure valid fernet key
    try:
        return Fernet(key.encode())
    except Exception:
        key = Fernet.generate_key().decode()
        return Fernet(key.encode())


def encrypt_token(token: str) -> str:
    f = get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(token_cipher: str) -> str:
    f = get_fernet()
    return f.decrypt(token_cipher.encode()).decode()
