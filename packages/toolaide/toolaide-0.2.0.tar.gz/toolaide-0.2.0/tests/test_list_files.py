"""Unit tests for the list_files tool."""

from toolaide.tools.list_files import tool_list_files


def test_list_files_basic(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    result = tool_list_files({"path": "."}, tmp_path)
    assert "f a.txt" in result
    assert "d subdir" in result


def test_list_files_empty_dir(tmp_path):
    result = tool_list_files({"path": "."}, tmp_path)
    assert result == "(empty directory)"


def test_list_files_not_a_directory(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    result = tool_list_files({"path": "file.txt"}, tmp_path)
    assert result.startswith("Error:")


def test_list_files_sorted(tmp_path):
    for name in ["c.txt", "a.txt", "b.txt"]:
        (tmp_path / name).write_text("")
    result = tool_list_files({"path": "."}, tmp_path)
    lines = result.splitlines()
    assert lines == ["f a.txt", "f b.txt", "f c.txt"]
