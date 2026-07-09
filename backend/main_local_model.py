# coding=utf-8
"""Local model service entrypoint (SERVER_NAME=local_model).

Runs as an independent FastAPI process bound to LOCAL_MODEL_HOST:LOCAL_MODEL_PORT,
mirroring the legacy `SERVER_NAME=local_model` profile. Only model-serving
routers are mounted when `settings.is_local_model` is True.
"""
import os

import uvicorn

from app.core.config import get_settings
from app.main import app

os.environ.setdefault("SERVER_NAME", "local_model")


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.local_model_host,
        port=settings.local_model_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
