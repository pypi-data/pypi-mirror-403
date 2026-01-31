"""Tests for state module."""

from cgc_common.state import JSONStore, XDGStateStore, merge_defaults


class TestMergeDefaults:
    def test_merge_empty_data(self):
        result = merge_defaults({}, {"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_partial_data(self):
        result = merge_defaults({"a": 10}, {"a": 1, "b": 2})
        assert result == {"a": 10, "b": 2}

    def test_merge_complete_data(self):
        result = merge_defaults({"a": 10, "b": 20}, {"a": 1, "b": 2})
        assert result == {"a": 10, "b": 20}


class TestJSONStore:
    def test_load_missing_file(self, tmp_path):
        store = JSONStore(path=tmp_path / "missing.json", defaults={"x": 1})
        assert store.load() == {"x": 1}

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "test.json"
        store = JSONStore(path=path)
        store.save({"key": "value"})
        assert store.load() == {"key": "value"}

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "test.json"
        store = JSONStore(path=path)
        store.save({"nested": True})
        assert path.exists()

    def test_load_merges_defaults(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text('{"existing": true}')
        store = JSONStore(path=path, defaults={"existing": False, "new": "default"})
        result = store.load()
        assert result == {"existing": True, "new": "default"}

    def test_update(self, tmp_path):
        path = tmp_path / "test.json"
        store = JSONStore(path=path, defaults={"a": 1, "b": 2})
        result = store.update({"b": 20})
        assert result == {"a": 1, "b": 20}
        # Verify persisted
        assert store.load() == {"a": 1, "b": 20}

    def test_invalid_json_returns_defaults(self, tmp_path):
        path = tmp_path / "invalid.json"
        path.write_text("not json")
        store = JSONStore(path=path, defaults={"fallback": True})
        assert store.load() == {"fallback": True}


class TestXDGStateStore:
    def test_get_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app")
        assert store.get_path() == tmp_path / "test_app" / "state.json"

    def test_custom_filename(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app", filename="settings.json")
        assert store.get_path() == tmp_path / "test_app" / "settings.json"

    def test_save_and_load(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app", defaults={"default": True})
        store.save({"saved": True})
        assert store.load() == {"saved": True, "default": True}

    def test_update(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app", defaults={"a": 1})
        result = store.update({"a": 10, "b": 2})
        assert result == {"a": 10, "b": 2}

    def test_exists(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app")
        assert not store.exists()
        store.save({})
        assert store.exists()

    def test_delete(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        store = XDGStateStore(app_name="test_app")
        store.save({"data": True})
        assert store.exists()
        assert store.delete() is True
        assert not store.exists()
        assert store.delete() is False  # Already deleted
