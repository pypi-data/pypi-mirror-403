"""Tests for config module."""

import pytest
from cgc_common.config import env_str, env_int, env_bool, BaseConfig


class TestEnvStr:
    def test_default_value(self):
        assert env_str("NONEXISTENT_VAR", "default") == "default"

    def test_existing_value(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "hello")
        assert env_str("TEST_VAR", "default") == "hello"

    def test_empty_default(self):
        assert env_str("NONEXISTENT_VAR") == ""


class TestEnvInt:
    def test_default_value(self):
        assert env_int("NONEXISTENT_VAR", 42) == 42

    def test_existing_value(self, monkeypatch):
        monkeypatch.setenv("TEST_INT", "123")
        assert env_int("TEST_INT", 0) == 123

    def test_invalid_int_returns_default(self, monkeypatch):
        monkeypatch.setenv("TEST_INT", "not_a_number")
        assert env_int("TEST_INT", 42) == 42

    def test_zero_default(self):
        assert env_int("NONEXISTENT_VAR") == 0


class TestEnvBool:
    def test_default_false(self):
        assert env_bool("NONEXISTENT_VAR") is False

    def test_default_true(self):
        assert env_bool("NONEXISTENT_VAR", True) is True

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YES", "on", "ON"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("TEST_BOOL", value)
        assert env_bool("TEST_BOOL") is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "NO", "off", "OFF", ""])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("TEST_BOOL", value)
        assert env_bool("TEST_BOOL", True) is False


class TestBaseConfig:
    def test_prefixed_key(self):
        class MyConfig(BaseConfig):
            APP_PREFIX = "MYAPP"

        assert MyConfig.prefixed_key("PORT") == "MYAPP_PORT"

    def test_prefixed_int(self, monkeypatch):
        class MyConfig(BaseConfig):
            APP_PREFIX = "MYAPP"

        monkeypatch.setenv("MYAPP_PORT", "8080")
        assert MyConfig.prefixed_int("PORT", 7865) == 8080

    def test_prefixed_bool(self, monkeypatch):
        class MyConfig(BaseConfig):
            APP_PREFIX = "MYAPP"

        monkeypatch.setenv("MYAPP_DEBUG", "1")
        assert MyConfig.prefixed_bool("DEBUG") is True
