from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .api.v1 import auth, engagement, health, polls, stream, suggestions
from .api.errors import APIError, api_error_handler
from .config import settings
from . import state

@asynccontextmanager
async def lifespan(app: FastAPI):
    from .services import cleanup, listening, maintenance
    import asyncio
    from .db.session import AsyncSessionLocal
    from .db.models import TwitchAccount
    from sqlalchemy import select
    import logging

    logger = logging.getLogger("lifecycle")
    try:
        settings.validate_settings()
        logger.info("Configuration validated successfully.")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        # In a real production app, we might want to exit the process here.
        # For now, we log it and proceed, but most routes will fail due to missing keys.

    asyncio.create_task(maintenance.validate_all_tokens())
    asyncio.create_task(listening.start_snapshot_loop(state.listener_manager))
    asyncio.create_task(cleanup.start_cleanup_loop())
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TwitchAccount).where(TwitchAccount.listening_desired == True))
        for acc in res.scalars():
            try:
                await state.listener_manager.start_listener(acc.id)
            except Exception:
                pass
    yield
    await state.listener_manager.stop_all()


app = FastAPI(title="Live Engagement Coach", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(APIError, api_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(stream.router, prefix="/api/v1")
app.include_router(engagement.router, prefix="/api/v1")
app.include_router(suggestions.router, prefix="/api/v1")
app.include_router(polls.router, prefix="/api/v1")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Live Engagement Coach Backend",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
