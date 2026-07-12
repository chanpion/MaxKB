"""Locale API — external locale discovery and loading.

Matches the old Django ``/locales/index.json`` and ``/locales/{code}.json``
endpoints that the frontend polls for overriding built-in translations.
"""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["locales"])

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "locales")


@router.get("/index.json")
async def locale_index() -> dict:
    """Return the set of available external locale overrides."""
    if not os.path.isdir(LOCALES_DIR):
        return {"locales": []}

    codes = sorted(d for d in os.listdir(LOCALES_DIR) if os.path.isdir(os.path.join(LOCALES_DIR, d)))
    return {"locales": codes}


@router.get("/{locale_code}.json")
async def locale_data(locale_code: str) -> dict:
    """Return the merged locale translations for *locale_code*."""
    path = os.path.join(LOCALES_DIR, locale_code, "LC_MESSAGES")
    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Locale not found")

    # Try to load a pre-built JSON translation file; Django .po files
    # are not directly consumable from the frontend.
    json_path = os.path.join(path, "django.json")
    if os.path.isfile(json_path):
        with open(json_path, encoding="utf-8") as fh:
            return json.load(fh)

    return {}
