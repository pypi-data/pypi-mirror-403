"""Unit tests for the search_files tool."""

from toolaide.tools.search_files import tool_search_files


def test_search_basic(tmp_path):
    (tmp_path / "a.py").write_text("def hello():\n    pass\n")
    result = tool_search_files({"pattern": "hello"}, tmp_path)
    assert "a.py:1:" in result
    assert "def hello()" in result


def test_search_no_matches(tmp_path):
    (tmp_path / "a.txt").write_text("nothing here")
    result = tool_search_files({"pattern": "zzz_missing"}, tmp_path)
    assert result == "No matches found."


def test_search_glob_filter(tmp_path):
    (tmp_path / "a.py").write_text("match\n")
    (tmp_path / "b.txt").write_text("match\n")
    result = tool_search_files({"pattern": "match", "glob": "*.py"}, tmp_path)
    assert "a.py" in result
    assert "b.txt" not in result


def test_search_regex(tmp_path):
    (tmp_path / "code.py").write_text("value = 42\nvalue = 99\n")
    result = tool_search_files({"pattern": r"value\s*=\s*\d+"}, tmp_path)
    assert "code.py:1:" in result
    assert "code.py:2:" in result


def test_search_max_results(tmp_path):
    # Create a file with >200 matching lines
    content = "\n".join(f"line {i} match" for i in range(250))
    (tmp_path / "big.txt").write_text(content)
    result = tool_search_files({"pattern": "match"}, tmp_path)
    assert "... (truncated)" in result
