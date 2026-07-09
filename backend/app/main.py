"""FastAPI application factory + lifespan.

The app is created once and reused by both the web entrypoint (`main.py`) and the
local-model entrypoint (`main_local_model.py`). Model-only routers are mounted
conditionally on `settings.is_local_model` in later stages.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.application import router as application_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.models import router as model_router
from app.api.system import router as system_router
from app.api.tools import router as tool_router
from app.api.trigger import router as trigger_router
from app.core.config import get_settings
from app.core.db import engine
from app.core.i18n import init_i18n
from app.core.redis import redis_client
from app.local_model.router import router as local_model_router
from app.tools.builtin import register_builtin_tools
from app.trigger.handlers import register_trigger_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_i18n(settings.language_code)
    # Wire trigger handlers + builtin tools so scheduled/event triggers and
    # workflow tool nodes can actually execute (previously no-ops).
    register_builtin_tools()
    register_trigger_handlers()
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
    app.include_router(auth_router)
    app.include_router(knowledge_router)
    app.include_router(model_router)
    app.include_router(application_router)
    app.include_router(tool_router)
    app.include_router(system_router)
    app.include_router(trigger_router)
    app.include_router(local_model_router)
    return app


app = create_app()
