# coding=utf-8
"""FastAPI application factory + lifespan.

The app is created once and reused by both the web entrypoint (`main.py`) and the
local-model entrypoint (`main_local_model.py`). Model-only routers are mounted
conditionally on `settings.is_local_model` in later stages.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.db import engine
from app.core.i18n import init_i18n
from app.core.redis import redis_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_i18n(settings.language_code)
    try:
        await redis_client.ping()
    except Exception:
        # Non-fatal in scaffold; a real deployment should fail fast.
        pass
    yield
    await redis_client.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="MaxKB Backend", version="2.0.0", lifespan=lifespan)
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()
