# coding=utf-8
"""i18n helpers (gettext/polib), reusing the existing locale catalogs."""
import gettext
from pathlib import Path

from app.core.config import get_settings

_settings = get_settings()
LOCALE_DIR = Path(_settings.external_locale_path)
_current: gettext.NullTranslations = gettext.NullTranslations()


def init_i18n(lang: str | None = None) -> None:
    global _current
    lang = lang or _settings.language_code
    try:
        _current = gettext.translation("django", localedir=LOCALE_DIR, languages=[lang])
    except FileNotFoundError:
        _current = gettext.NullTranslations()


def _(message: str) -> str:
    return _current.gettext(message)
