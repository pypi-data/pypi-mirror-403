"""Tests for path sanitization module."""

from pathlib import Path

import pytest
from cgc_common.utils.paths import (
    PathTraversalError,
    is_safe_path,
    normalize_path,
    resolve_safe_path,
    safe_join,
    sanitize_filename,
)


class TestSanitizeFilename:
    def test_simple_filename(self):
        assert sanitize_filename("file.txt") == "file.txt"

    def test_removes_directory_traversal(self):
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result == "passwd"

    def test_removes_absolute_path(self):
        result = sanitize_filename("/etc/passwd")
        assert result == "passwd"

    def test_replaces_dangerous_chars(self):
        result = sanitize_filename('file<with>bad:chars?.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "?" not in result

    def test_removes_null_bytes(self):
        result = sanitize_filename("file\x00.txt")
        assert "\x00" not in result

    def test_strips_dots_and_spaces(self):
        assert sanitize_filename("...file.txt...") == "file.txt"
        assert sanitize_filename("  file.txt  ") == "file.txt"

    def test_handles_windows_reserved_names(self):
        result = sanitize_filename("CON")
        assert result == "_CON"
        result = sanitize_filename("con.txt")
        assert result == "_con.txt"
        result = sanitize_filename("NUL")
        assert result == "_NUL"

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_filename("")

    def test_only_dots_raises(self):
        with pytest.raises(ValueError, match="empty after sanitization"):
            sanitize_filename("...")

    def test_backslash_windows_path(self):
        result = sanitize_filename("folder\\file.txt")
        assert "\\" not in result


class TestIsSafePath:
    def test_safe_subpath(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        assert is_safe_path(subdir, tmp_path) is True

    def test_safe_file(self, tmp_path):
        file = tmp_path / "file.txt"
        file.touch()
        assert is_safe_path(file, tmp_path) is True

    def test_traversal_attack(self, tmp_path):
        evil_path = tmp_path / ".." / ".." / "etc" / "passwd"
        assert is_safe_path(evil_path, tmp_path) is False

    def test_same_path(self, tmp_path):
        assert is_safe_path(tmp_path, tmp_path) is True

    def test_absolute_outside(self, tmp_path):
        assert is_safe_path("/etc/passwd", tmp_path) is False

    def test_symlink_escape(self, tmp_path):
        # Create a symlink pointing outside base_dir
        target = Path("/tmp")
        link = tmp_path / "escape_link"
        try:
            link.symlink_to(target)
            assert is_safe_path(link, tmp_path) is False
        except OSError:
            pytest.skip("Cannot create symlink")


class TestResolveSafePath:
    def test_relative_path(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = resolve_safe_path("subdir", tmp_path)
        assert result == subdir

    def test_nested_relative(self, tmp_path):
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        result = resolve_safe_path("a/b", tmp_path)
        assert result == nested

    def test_traversal_raises(self, tmp_path):
        with pytest.raises(PathTraversalError):
            resolve_safe_path("../../../etc/passwd", tmp_path)

    def test_absolute_inside(self, tmp_path):
        file = tmp_path / "file.txt"
        file.touch()
        result = resolve_safe_path(str(file), tmp_path)
        assert result == file

    def test_absolute_outside_raises(self, tmp_path):
        with pytest.raises(PathTraversalError):
            resolve_safe_path("/etc/passwd", tmp_path)

    def test_must_exist_true(self, tmp_path):
        existing = tmp_path / "exists.txt"
        existing.touch()
        result = resolve_safe_path("exists.txt", tmp_path, must_exist=True)
        assert result == existing

    def test_must_exist_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            resolve_safe_path("missing.txt", tmp_path, must_exist=True)

    def test_must_exist_false_allows_missing(self, tmp_path):
        result = resolve_safe_path("new_file.txt", tmp_path, must_exist=False)
        assert result == tmp_path / "new_file.txt"


class TestSafeJoin:
    def test_simple_join(self, tmp_path):
        result = safe_join(tmp_path, "file.txt")
        assert result == tmp_path / "file.txt"

    def test_nested_join(self, tmp_path):
        result = safe_join(tmp_path, "a", "b", "c.txt")
        assert result == tmp_path / "a" / "b" / "c.txt"

    def test_traversal_in_parts(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(tmp_path, "safe", "..", "..", "escape")

    def test_absolute_in_parts_raises(self, tmp_path):
        with pytest.raises(PathTraversalError, match="Absolute path not allowed"):
            safe_join(tmp_path, "/etc/passwd")

    def test_empty_parts(self, tmp_path):
        result = safe_join(tmp_path)
        assert result == tmp_path


class TestNormalizePath:
    def test_expands_user(self):
        result = normalize_path("~/test")
        assert "~" not in str(result)
        assert result.is_absolute()

    def test_resolves_relative(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = normalize_path("./subdir/../file.txt")
        assert result == tmp_path / "file.txt"

    def test_absolute_unchanged(self):
        result = normalize_path("/absolute/path")
        assert result == Path("/absolute/path")


class TestPathTraversalError:
    def test_is_value_error(self):
        error = PathTraversalError("test")
        assert isinstance(error, ValueError)

    def test_message(self):
        error = PathTraversalError("Path escaped!")
        assert str(error) == "Path escaped!"
