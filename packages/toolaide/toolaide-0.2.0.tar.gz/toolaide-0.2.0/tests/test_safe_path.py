"""Unit tests for the _safe_path helper."""

import pytest
from toolaide.tools.common import _safe_path


def test_safe_path_valid(tmp_path):
    result = _safe_path(tmp_path, "subdir/file.txt")
    assert str(result).startswith(str(tmp_path.resolve()))


def test_safe_path_dot(tmp_path):
    result = _safe_path(tmp_path, ".")
    assert result == tmp_path.resolve()


def test_safe_path_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match="Path escapes workspace"):
        _safe_path(tmp_path, "../etc/passwd")


def test_safe_path_rejects_absolute(tmp_path):
    with pytest.raises(ValueError, match="Path escapes workspace"):
        _safe_path(tmp_path, "/etc/passwd")
