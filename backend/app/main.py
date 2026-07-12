"""FastAPI application factory + lifespan.

The app is created once and reused by both the web entrypoint (`main.py`) and the
local-model entrypoint (`main_local_model.py`). Model-only routers are mounted
conditionally on `settings.is_local_model` in later stages.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.application import router as application_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.homepage import router as homepage_router
from app.api.knowledge import router as knowledge_router
from app.api.locales import router as locales_router
from app.api.models import router as model_router
from app.api.oss import router as oss_router
from app.api.system import router as system_router
from app.api.tools import router as tool_router
from app.api.trigger import router as trigger_router
from app.core.config import get_settings
from app.core.db import engine
from app.core.i18n import init_i18n
from app.core.redis import redis_client
from app.local_model.router import router as local_model_router
from app.middleware.path_rewrite import PathRewriteMiddleware
from app.middleware.response_format import LegacyResponseMiddleware
from app.tools.builtin import register_builtin_tools
from app.trigger.handlers import register_trigger_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_i18n(settings.language_code)
    register_builtin_tools()
    register_trigger_handlers()
    try:
        await redis_client.ping()
    except Exception:
        pass
    yield
    await redis_client.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="MaxKB Backend", version="2.0.0", lifespan=lifespan)

    # Middleware (added first → innermost, added last → outermost).
    # Response chain (out→in): PathRewrite → GZip → LegacyResponse → CORS → route.
    # We keep GZip OUTSIDE LegacyResponse so the JSON envelope produced by
    # LegacyResponseMiddleware is compressed as a whole, and LegacyResponse always
    # sees the *uncompressed* JSON body (otherwise GZip would hand it gzip bytes).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Response format wrapper (must run on the uncompressed body)
    app.add_middleware(LegacyResponseMiddleware)

    # GZip compresses the wrapped response on the way out
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Path rewrite middleware — must be *last* added so it is outermost and
    # runs first, rewriting the path before any other middleware or router sees it.
    app.add_middleware(
        PathRewriteMiddleware,
        admin_prefix=settings.api_prefix,
        chat_prefix=settings.chat_api_prefix,
    )

    # Routers
    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router)
    app.include_router(homepage_router)
    app.include_router(knowledge_router)
    app.include_router(model_router)
    app.include_router(oss_router)
    app.include_router(application_router)
    app.include_router(chat_router)
    app.include_router(tool_router)
    app.include_router(system_router)
    app.include_router(trigger_router)
    app.include_router(local_model_router)
    # Locale files (served under /admin/locales and /chat/locales)
    app.include_router(locales_router, prefix="/admin/locales")
    app.include_router(locales_router, prefix="/chat/locales")
    return app


app = create_app()
