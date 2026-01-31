"""
Internationalization utilities for Cindergrace applications.

Provides:
- YAML translation file loading
- Simple translation manager for non-Gradio contexts
- Integration helpers for gradio_i18n

Translation File Format (YAML):
    en:
      greeting: "Hello"
      farewell: "Goodbye"
    de:
      greeting: "Hallo"
      farewell: "Auf Wiedersehen"

Usage with Gradio (recommended):
    from gradio_i18n import Translate, gettext as _
    from cgc_common import get_translations_path

    with Translate(get_translations_path(), placeholder_langs=["en", "de"]) as lang:
        gr.Button(_("apply"))  # -> "Apply" or "Anwenden"

Usage without Gradio:
    from cgc_common import I18nManager

    i18n = I18nManager("path/to/translations.yaml", default_lang="en")
    i18n.set_language("de")
    print(i18n.t("greeting"))  # -> "Hallo"
"""

from pathlib import Path
from typing import Any

import yaml


def load_translations(path: str | Path) -> dict[str, dict[str, str]]:
    """Load translations from YAML file.

    Args:
        path: Path to YAML translation file

    Returns:
        Dict with language codes as keys and translation dicts as values

    Example:
        translations = load_translations("i18n/ui.yaml")
        # {"en": {"greeting": "Hello"}, "de": {"greeting": "Hallo"}}
    """
    path = Path(path)
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data if isinstance(data, dict) else {}


class I18nManager:
    """Simple translation manager for non-Gradio contexts.

    For Gradio applications, use gradio_i18n instead. This class
    is useful for CLI tools, logging, or backend services.

    Example:
        i18n = I18nManager("translations.yaml", default_lang="en")
        i18n.set_language("de")

        # Simple translation
        print(i18n.t("greeting"))  # -> "Hallo"

        # With fallback
        print(i18n.t("unknown_key"))  # -> "unknown_key"

        # Context manager for temporary language switch
        with i18n.language("en"):
            print(i18n.t("greeting"))  # -> "Hello"
    """

    def __init__(
        self,
        translations_path: str | Path | None = None,
        translations: dict[str, dict[str, str]] | None = None,
        default_lang: str = "en",
    ):
        """Initialize translation manager.

        Args:
            translations_path: Path to YAML translation file
            translations: Pre-loaded translations dict (alternative to path)
            default_lang: Default language code
        """
        if translations is not None:
            self._translations = translations
        elif translations_path is not None:
            self._translations = load_translations(translations_path)
        else:
            self._translations = {}

        self._current_lang = default_lang
        self._default_lang = default_lang

    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_lang

    @property
    def available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(self._translations.keys())

    def set_language(self, lang: str) -> None:
        """Set current language.

        Args:
            lang: Language code (e.g., "en", "de")
        """
        if lang in self._translations:
            self._current_lang = lang

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key.

        Args:
            key: Translation key
            **kwargs: Format arguments for string interpolation

        Returns:
            Translated string, or key if not found
        """
        # Try current language
        lang_dict = self._translations.get(self._current_lang, {})
        value = lang_dict.get(key)

        # Fallback to default language
        if value is None and self._current_lang != self._default_lang:
            lang_dict = self._translations.get(self._default_lang, {})
            value = lang_dict.get(key)

        # Final fallback: return key
        if value is None:
            return key

        # Apply format arguments if any
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value

        return value

    def language(self, lang: str):
        """Context manager for temporary language switch.

        Args:
            lang: Language code to use temporarily

        Returns:
            Context manager that restores original language on exit
        """
        return _LanguageContext(self, lang)


class _LanguageContext:
    """Context manager for temporary language switch."""

    def __init__(self, manager: I18nManager, lang: str):
        self._manager = manager
        self._new_lang = lang
        self._old_lang = manager.current_language

    def __enter__(self):
        self._manager.set_language(self._new_lang)
        return self._manager

    def __exit__(self, *args):
        self._manager.set_language(self._old_lang)


def get_translations_path(app_path: Path, filename: str = "ui.yaml") -> Path:
    """Get standard translations file path for an app.

    Checks common locations:
    1. {app_path}/i18n/{filename}
    2. {app_path}/translations/{filename}
    3. {app_path}/{filename}

    Args:
        app_path: Application root directory
        filename: Translation filename (default: ui.yaml)

    Returns:
        Path to translation file

    Raises:
        FileNotFoundError: If no translation file found
    """
    candidates = [
        app_path / "i18n" / filename,
        app_path / "translations" / filename,
        app_path / filename,
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"No translation file found. Checked: {', '.join(str(p) for p in candidates)}"
    )
