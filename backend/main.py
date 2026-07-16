# coding=utf-8
"""Web entrypoint (SERVER_NAME=web).

Starts the FastAPI service on 0.0.0.0:8080, mirroring the legacy Django
runserver port. Use a reverse proxy / gateway to coexist with the legacy service.
"""
import os

import uvicorn

from app.core.config import get_settings

os.environ.setdefault("SERVER_NAME", "web")


def main() -> None:
    settings = get_settings()
    uvicorn.run("app.main:app",
                host=settings.web_host,
                port=settings.web_port,
                log_level=settings.log_level.lower(),
                reload=True
                )


if __name__ == "__main__":
    main()
