from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TWITCH_CLIENT_ID: str = ""
    TWITCH_CLIENT_SECRET: str = ""
    TWITCH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/twitch/callback"
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    FRONTEND_SUCCESS_URL: str = "http://localhost:5173/connected"
    DATABASE_URL: str = "postgresql+asyncpg://coach:coach@postgres:5432/coach"
    TOKEN_ENCRYPTION_KEY: str = ""
    SESSION_PEPPER: str = ""
    CHATTER_HASH_PEPPER: str = ""
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None
    OPENAI_TIMEOUT_SECONDS: int = 8

    def validate_settings(self):
        """Verify that essential secrets are provided and valid."""
        missing = []
        if not self.TWITCH_CLIENT_ID: missing.append("TWITCH_CLIENT_ID")
        if not self.TWITCH_CLIENT_SECRET: missing.append("TWITCH_CLIENT_SECRET")
        if not self.TOKEN_ENCRYPTION_KEY: missing.append("TOKEN_ENCRYPTION_KEY")
        if not self.SESSION_PEPPER: missing.append("SESSION_PEPPER")
        if not self.CHATTER_HASH_PEPPER: missing.append("CHATTER_HASH_PEPPER")
        
        if missing:
            raise ValueError(f"Missing essential environment variables: {', '.join(missing)}")
        
        try:
            Fernet(self.TOKEN_ENCRYPTION_KEY.encode())
        except Exception:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be a valid Fernet key (32 url-safe base64-encoded bytes)")

    def get_openai_config(self):
        """Check if OpenAI is usable."""
        if not self.OPENAI_API_KEY or not self.OPENAI_MODEL:
            return None
        return {"key": self.OPENAI_API_KEY, "model": self.OPENAI_MODEL}

settings = Settings()
