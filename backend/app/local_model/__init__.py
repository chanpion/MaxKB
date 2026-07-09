"""Local model service (SERVER_NAME=local_model).

Mirrors the legacy ``local_model`` profile: an OpenAI-compatible inference
server (vLLM / llama.cpp / Ollama) is hosted behind ``local_model_host:port``
and exposed to the rest of MaxKB through the standard ``/v1`` surface. The
migration does not re-implement the inference server — it proxies to it so the
web process can call ``/api/local_model/v1/chat/completions`` exactly as before.
"""

from app.local_model.router import router

__all__ = ["router"]
