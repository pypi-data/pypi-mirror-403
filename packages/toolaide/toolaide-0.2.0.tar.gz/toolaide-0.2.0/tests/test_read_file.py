"""Unit tests for the read_file tool."""

from toolaide.tools.read_file import tool_read_file


def test_read_file_basic(tmp_path):
    (tmp_path / "hello.txt").write_text("hello world")
    result = tool_read_file({"path": "hello.txt"}, tmp_path)
    assert result == "hello world"


def test_read_file_not_found(tmp_path):
    result = tool_read_file({"path": "missing.txt"}, tmp_path)
    assert result.startswith("Error:")


def test_read_file_truncation(tmp_path):
    content = "x" * 60_000
    (tmp_path / "big.txt").write_text(content)
    result = tool_read_file({"path": "big.txt"}, tmp_path)
    assert len(result) < 60_000
    assert "... (truncated)" in result


def test_read_file_encoding_errors(tmp_path):
    # Write raw bytes that aren't valid UTF-8
    (tmp_path / "binary.bin").write_bytes(b"\x80\x81\x82hello")
    result = tool_read_file({"path": "binary.bin"}, tmp_path)
    assert "hello" in result
