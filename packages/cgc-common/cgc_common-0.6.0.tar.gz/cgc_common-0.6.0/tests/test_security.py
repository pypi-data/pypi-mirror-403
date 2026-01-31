"""Tests for security module."""

from cgc_common.config import BaseConfig
from cgc_common.security import SecurityMixin


class TestSecurityMixin:
    def test_default_localhost(self):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "TEST"

        assert Config.get_server_bind() == "127.0.0.1"
        assert Config.allow_remote() is False

    def test_allow_remote(self, monkeypatch):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "TEST"

        monkeypatch.setenv("TEST_ALLOW_REMOTE", "1")
        assert Config.allow_remote() is True
        assert Config.get_server_bind() == "0.0.0.0"

    def test_feature_disabled_by_default(self):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "TEST"

        assert Config.is_feature_enabled("KILL") is False
        assert Config.is_feature_enabled("PACKAGES") is False

    def test_feature_enabled(self, monkeypatch):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "TEST"

        monkeypatch.setenv("TEST_ENABLE_KILL", "1")
        assert Config.is_feature_enabled("KILL") is True
        assert Config.is_feature_enabled("PACKAGES") is False

    def test_feature_case_insensitive(self, monkeypatch):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "TEST"

        monkeypatch.setenv("TEST_ENABLE_KILL", "1")
        assert Config.is_feature_enabled("kill") is True
        assert Config.is_feature_enabled("Kill") is True

    def test_security_docs(self):
        class Config(BaseConfig, SecurityMixin):
            APP_PREFIX = "MYAPP"

        docs = Config.get_security_docs()
        assert "MYAPP_ALLOW_REMOTE" in docs
