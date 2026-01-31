"""Unit tests for common helper functions."""

from toolaide.tools.common import is_ignored, _load_gitignore


def test_is_ignored_no_gitignore(tmp_path):
    """Returns False when no .gitignore exists."""
    _load_gitignore.cache_clear()
    assert is_ignored(tmp_path, "any_file.txt") is False


def test_is_ignored_nested_file_by_name(tmp_path):
    """Matches files listed by name in nested directories."""
    _load_gitignore.cache_clear()
    (tmp_path / ".gitignore").write_text("secret.env\n")

    # Root level
    assert is_ignored(tmp_path, "secret.env") is True
    # Nested paths
    assert is_ignored(tmp_path, "config/secret.env") is True
    assert is_ignored(tmp_path, "src/config/secret.env") is True
    # Different filename should not match
    assert is_ignored(tmp_path, "config/other.env") is False


def test_is_ignored_nested_directory_by_name(tmp_path):
    """Matches directories listed by name at any depth."""
    _load_gitignore.cache_clear()
    (tmp_path / ".gitignore").write_text("node_modules/\n__pycache__/\n")

    # Root level
    assert is_ignored(tmp_path, "node_modules/") is True
    assert is_ignored(tmp_path, "__pycache__/") is True
    # Nested directories
    assert is_ignored(tmp_path, "frontend/node_modules/") is True
    assert is_ignored(tmp_path, "src/utils/__pycache__/") is True
    # Files inside ignored dirs
    assert is_ignored(tmp_path, "node_modules/package.json") is True
    assert is_ignored(tmp_path, "lib/sub/__pycache__/cache.pyc") is True


def test_is_ignored_wildcard_extension(tmp_path):
    """Matches wildcard patterns in nested directories."""
    _load_gitignore.cache_clear()
    (tmp_path / ".gitignore").write_text("*.pyc\n*.log\n")

    assert is_ignored(tmp_path, "module.pyc") is True
    assert is_ignored(tmp_path, "src/deep/nested/module.pyc") is True
    assert is_ignored(tmp_path, "logs/app.log") is True
    assert is_ignored(tmp_path, "src/module.py") is False


def test_is_ignored_does_not_match_unrelated(tmp_path):
    """Ensures non-matching files are not ignored."""
    _load_gitignore.cache_clear()
    (tmp_path / ".gitignore").write_text("build/\n*.tmp\n")

    assert is_ignored(tmp_path, "src/main.py") is False
    assert is_ignored(tmp_path, "deep/nested/file.txt") is False
    assert is_ignored(tmp_path, "rebuild/output") is False


def test_is_ignored_nested_gitignore_not_supported(tmp_path):
    """Nested .gitignore files are not read (only root .gitignore is used)."""
    _load_gitignore.cache_clear()
    (tmp_path / ".gitignore").write_text("*.log\n")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / ".gitignore").write_text("secret.txt\n")

    # Root .gitignore works
    assert is_ignored(tmp_path, "subdir/app.log") is True
    # Nested .gitignore is ignored - secret.txt is NOT filtered out
    assert is_ignored(tmp_path, "subdir/secret.txt") is False
