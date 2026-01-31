"""Tools package — exports TOOLS list and TOOL_DISPATCH dict."""

from .list_files import TOOL_DEFINITION as LIST_FILES_TOOL, tool_list_files
from .search_files import TOOL_DEFINITION as SEARCH_FILES_TOOL, tool_search_files
from .read_file import TOOL_DEFINITION as READ_FILE_TOOL, tool_read_file
from .write_file import TOOL_DEFINITION as WRITE_FILE_TOOL, tool_write_file

TOOLS = [LIST_FILES_TOOL, SEARCH_FILES_TOOL, READ_FILE_TOOL, WRITE_FILE_TOOL]

TOOL_DISPATCH = {
    "list_files": tool_list_files,
    "search_files": tool_search_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
}
