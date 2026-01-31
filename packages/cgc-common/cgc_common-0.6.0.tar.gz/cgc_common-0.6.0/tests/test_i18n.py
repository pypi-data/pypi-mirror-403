"""Tests for i18n module."""

import pytest
from cgc_common.i18n import I18nManager


class TestI18nManager:
    @pytest.fixture
    def translations(self):
        return {
            "en": {
                "greeting": "Hello",
                "farewell": "Goodbye",
                "with_arg": "Hello, {name}!",
            },
            "de": {
                "greeting": "Hallo",
                "farewell": "Auf Wiedersehen",
                "with_arg": "Hallo, {name}!",
            },
        }

    def test_default_language(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        assert i18n.current_language == "en"
        assert i18n.t("greeting") == "Hello"

    def test_set_language(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        i18n.set_language("de")
        assert i18n.current_language == "de"
        assert i18n.t("greeting") == "Hallo"

    def test_fallback_to_key(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        assert i18n.t("nonexistent_key") == "nonexistent_key"

    def test_fallback_to_default_language(self, translations):
        # Add a key only in English
        translations["en"]["english_only"] = "Only in English"
        i18n = I18nManager(translations=translations, default_lang="en")
        i18n.set_language("de")
        assert i18n.t("english_only") == "Only in English"

    def test_format_arguments(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        assert i18n.t("with_arg", name="World") == "Hello, World!"

    def test_available_languages(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        assert set(i18n.available_languages) == {"en", "de"}

    def test_language_context_manager(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        assert i18n.t("greeting") == "Hello"

        with i18n.language("de"):
            assert i18n.t("greeting") == "Hallo"

        # Should restore original language
        assert i18n.t("greeting") == "Hello"

    def test_ignore_invalid_language(self, translations):
        i18n = I18nManager(translations=translations, default_lang="en")
        i18n.set_language("fr")  # Not available
        assert i18n.current_language == "en"  # Should stay unchanged
