"""Application configuration.

Reads the legacy MaxKB ``MAXKB_*`` environment variables (prefix stripped by the
old ConfigManager) and the unprefixed ``SERVER_NAME`` role selector, plus an
optional ``.env`` file. Values mirror ``apps/maxkb/conf.py`` defaults so the new
backend can share the same PostgreSQL / Redis with the legacy Django service.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    # Service role: "web" | "local_model" (maps to Django SERVER_NAME).
    server_name: str = Field(default="web", alias="SERVER_NAME")

    # --- Database (PostgreSQL 17 + pgvector) ---
    db_host: str = Field(default="127.0.0.1", alias="MAXKB_DB_HOST")
    db_port: int = Field(default=5432, alias="MAXKB_DB_PORT")
    db_name: str = Field(default="maxkb", alias="MAXKB_DB_NAME")
    db_user: str = Field(default="root", alias="MAXKB_DB_USER")
    db_password: str = Field(default="Password123@postgres", alias="MAXKB_DB_PASSWORD")
    db_max_overflow: int = Field(default=80, alias="MAXKB_DB_MAX_OVERFLOW")

    # Connection pool (mapped from Django dj_db_conn_pool POOL_OPTIONS).
    db_pool_size: int = 20
    db_pool_recycle: int = 1800
    db_pool_timeout: int = 30
    db_pool_pre_ping: bool = True

    # --- Redis (cache + arq broker) ---
    redis_host: str = Field(default="127.0.0.1", alias="MAXKB_REDIS_HOST")
    redis_port: int = Field(default=6379, alias="MAXKB_REDIS_PORT")
    redis_password: str = Field(default="Password123@redis", alias="MAXKB_REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="MAXKB_REDIS_DB")
    redis_max_connections: int = Field(default=100, alias="MAXKB_REDIS_MAX_CONNECTIONS")
    redis_sentinel_sentinels: str | None = Field(default=None, alias="MAXKB_REDIS_SENTINEL_SENTINELS")
    redis_sentinel_master: str | None = Field(default=None, alias="MAXKB_REDIS_SENTINEL_MASTER")

    # --- Local model service (mirrors SERVER_NAME=local_model) ---
    local_model_host: str = Field(default="127.0.0.1", alias="MAXKB_LOCAL_MODEL_HOST")
    local_model_port: int = Field(default=11636, alias="MAXKB_LOCAL_MODEL_PORT")
    local_model_protocol: str = Field(default="http", alias="MAXKB_LOCAL_MODEL_PROTOCOL")
    local_model_host_worker: int = Field(default=1, alias="MAXKB_LOCAL_MODEL_HOST_WORKER")

    # --- Local embedding model (sentence-transformers) ---
    # Checkpoint used by the ``local`` embedding provider when no API key /
    # base_url is supplied. A local directory (e.g. a ModelScope snapshot) takes
    # priority over the built-in HuggingFace default. Empty = built-in default.
    local_embedding_model_path: str = Field(
        default="",
        alias="MAXKB_LOCAL_EMBEDDING_MODEL_PATH",
        description="Local sentence-transformers checkpoint (dir or HF id) for the 'local' embedding provider.",
    )

    # --- General ---
    debug: bool = Field(default=False, alias="MAXKB_DEBUG")
    web_host: str = Field(default="0.0.0.0", alias="MAXKB_WEB_HOST")
    web_port: int = Field(default=8080, alias="MAXKB_WEB_PORT")
    language_code: str = Field(default="zh-CN", alias="MAXKB_LANGUAGE_CODE")
    time_zone: str = Field(default="Asia/Shanghai", alias="MAXKB_TIME_ZONE")
    log_level: str = Field(default="DEBUG", alias="MAXKB_LOG_LEVEL")
    sandbox_python_package_paths: str = Field(
        default="/opt/py3/lib/python3.11/site-packages,"
        "/opt/maxkb-app/sandbox/python-packages,"
        "/opt/maxkb/python-packages",
        alias="MAXKB_SANDBOX_PYTHON_PACKAGE_PATHS",
    )
    admin_path: str = Field(default="/admin", alias="MAXKB_ADMIN_PATH")
    chat_path: str = Field(default="/chat", alias="MAXKB_CHAT_PATH")
    api_prefix: str = Field(default="/api", alias="MAXKB_API_PREFIX")
    chat_api_prefix: str = Field(default="/api", alias="MAXKB_CHAT_API_PREFIX")
    session_timeout: int = Field(default=28800, alias="MAXKB_SESSION_TIMEOUT")
    external_locale_path: str = Field(default="/opt/maxkb/local/locales", alias="MAXKB_EXTERNAL_LOCALE_PATH")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_local_model(self) -> bool:
        return self.server_name == "local_model"


@lru_cache
def get_settings() -> Settings:
    return Settings()
