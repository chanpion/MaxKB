# coding=utf-8
"""Web entrypoint (SERVER_NAME=web).

Starts the FastAPI service on 0.0.0.0:8080, mirroring the legacy Django
runserver port. Use a reverse proxy / gateway to coexist with the legacy service.
"""
import os

import uvicorn

from app.core.config import get_settings
from app.main import app

os.environ.setdefault("SERVER_NAME", "web")


def main() -> None:
    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
