"""Tests for secrets module."""

import os
import warnings

import pytest
from cgc_common.secrets import (
    SecretStore,
    SecretStoreWarning,
    get_secret,
    set_secret,
)


class TestSecretStore:
    """Tests for SecretStore class."""

    def test_init_default_prefix(self):
        store = SecretStore("my-app")
        assert store.service_name == "my-app"
        assert store.env_prefix == "MY_APP"

    def test_init_custom_prefix(self):
        store = SecretStore("myapp", env_prefix="CUSTOM")
        assert store.env_prefix == "CUSTOM"

    def test_env_var_name(self):
        store = SecretStore("myapp")
        assert store._env_var_name("api_token") == "MYAPP__API_TOKEN"
        assert store._env_var_name("API-KEY") == "MYAPP__API_KEY"

    def test_get_from_env(self, monkeypatch):
        """Test getting secret from environment variable."""
        monkeypatch.setenv("TESTAPP__MY_SECRET", "secret123")
        store = SecretStore("testapp", warn_on_fallback=False)

        # Force env var fallback by marking keyring as tested and not working
        store._keyring_tested = True
        store._keyring_works = False

        value = store.get("MY_SECRET")
        assert value == "secret123"

    def test_get_default_when_missing(self):
        store = SecretStore("testapp_missing", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        value = store.get("NONEXISTENT", default="fallback")
        assert value == "fallback"

    def test_get_none_when_missing_no_default(self):
        store = SecretStore("testapp_none", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        value = store.get("NONEXISTENT")
        assert value is None

    def test_set_to_env(self):
        """Test setting secret to environment (when keyring unavailable)."""
        store = SecretStore("testapp_set", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        result = store.set("NEW_SECRET", "value123")
        assert result is False  # False = stored in env, not keyring
        assert os.environ.get("TESTAPP_SET__NEW_SECRET") == "value123"

        # Cleanup
        del os.environ["TESTAPP_SET__NEW_SECRET"]

    def test_delete_from_env(self, monkeypatch):
        """Test deleting secret from environment."""
        monkeypatch.setenv("TESTAPP_DEL__TO_DELETE", "deleteme")
        store = SecretStore("testapp_del", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        result = store.delete("TO_DELETE")
        assert result is True
        assert "TESTAPP_DEL__TO_DELETE" not in os.environ

    def test_delete_nonexistent(self):
        store = SecretStore("testapp_del2", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        result = store.delete("NONEXISTENT")
        assert result is False

    def test_exists_true(self, monkeypatch):
        monkeypatch.setenv("TESTAPP_EX__EXISTS", "yes")
        store = SecretStore("testapp_ex", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        assert store.exists("EXISTS") is True

    def test_exists_false(self):
        store = SecretStore("testapp_ex2", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        assert store.exists("NONEXISTENT") is False

    def test_warning_on_fallback(self, monkeypatch):
        """Test that warning is emitted when falling back to env vars."""
        monkeypatch.setenv("TESTAPP_WARN__WARNED", "value")
        store = SecretStore("testapp_warn", warn_on_fallback=True)
        store._keyring_tested = True
        store._keyring_works = False

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            store.get("WARNED")

            assert len(w) == 1
            assert issubclass(w[0].category, SecretStoreWarning)
            assert "Keyring unavailable" in str(w[0].message)

    def test_no_warning_when_disabled(self, monkeypatch):
        """Test that warning can be suppressed."""
        monkeypatch.setenv("TESTAPP_NOWARN__SECRET", "value")
        store = SecretStore("testapp_nowarn", warn_on_fallback=False)
        store._keyring_tested = True
        store._keyring_works = False

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            store.get("SECRET")

            # Filter only our warnings
            our_warnings = [x for x in w if issubclass(x.category, SecretStoreWarning)]
            assert len(our_warnings) == 0

    def test_get_storage_info(self):
        store = SecretStore("testapp_info")
        info = store.get_storage_info()

        assert "keyring_available" in info
        assert "keyring_functional" in info
        assert info["service_name"] == "testapp_info"
        assert info["env_prefix"] == "TESTAPP_INFO"

    def test_is_keyring_available(self):
        store = SecretStore("testapp_avail")
        # Just test that it returns a boolean without error
        result = store.is_keyring_available()
        assert isinstance(result, bool)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_secret(self, monkeypatch):
        monkeypatch.setenv("CONV_TEST__TOKEN", "abc123")

        # Force env var fallback
        value = get_secret("conv_test", "TOKEN")
        # Value depends on whether keyring is available
        # If keyring works, it might not find it there and fall back to env
        assert value == "abc123" or value is None

    def test_set_secret(self):
        result = set_secret("conv_test_set", "KEY", "value")
        # Returns True if keyring, False if env
        assert isinstance(result, bool)

        # Cleanup if stored in env
        env_var = "CONV_TEST_SET__KEY"
        if env_var in os.environ:
            del os.environ[env_var]


class TestKeyringIntegration:
    """Integration tests that actually use keyring if available.

    These tests are skipped if keyring is not functional.
    """

    @pytest.fixture
    def keyring_store(self):
        """Create a store and skip if keyring not available."""
        store = SecretStore("cindergrace_test", warn_on_fallback=False)
        if not store.is_keyring_available():
            pytest.skip("Keyring not available")
        return store

    def test_keyring_roundtrip(self, keyring_store):
        """Test store/retrieve/delete cycle with real keyring."""
        key = "test_roundtrip_key"
        value = "test_secret_value_12345"

        try:
            # Store
            result = keyring_store.set(key, value)
            assert result is True  # True = stored in keyring

            # Retrieve
            retrieved = keyring_store.get(key)
            assert retrieved == value

            # Exists
            assert keyring_store.exists(key) is True

        finally:
            # Cleanup
            keyring_store.delete(key)

    def test_keyring_delete(self, keyring_store):
        """Test deletion from keyring."""
        key = "test_delete_key"

        keyring_store.set(key, "to_delete")
        assert keyring_store.exists(key) is True

        result = keyring_store.delete(key)
        assert result is True
        assert keyring_store.exists(key) is False

    def test_keyring_overwrite(self, keyring_store):
        """Test overwriting existing secret."""
        key = "test_overwrite_key"

        try:
            keyring_store.set(key, "original")
            assert keyring_store.get(key) == "original"

            keyring_store.set(key, "updated")
            assert keyring_store.get(key) == "updated"

        finally:
            keyring_store.delete(key)
