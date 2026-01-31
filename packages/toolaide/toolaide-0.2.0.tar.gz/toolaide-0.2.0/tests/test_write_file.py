"""Unit tests for the write_file tool."""

from toolaide.tools.write_file import tool_write_file


def test_write_file_basic(tmp_path):
    result = tool_write_file({"path": "out.txt", "content": "hello"}, tmp_path)
    assert "5 bytes" in result
    assert (tmp_path / "out.txt").read_text() == "hello"


def test_write_file_creates_parents(tmp_path):
    result = tool_write_file({"path": "a/b/c.txt", "content": "nested"}, tmp_path)
    assert (tmp_path / "a" / "b" / "c.txt").read_text() == "nested"


def test_write_file_overwrites(tmp_path):
    (tmp_path / "f.txt").write_text("old")
    tool_write_file({"path": "f.txt", "content": "new"}, tmp_path)
    assert (tmp_path / "f.txt").read_text() == "new"
