"""Search files tool — regex search across workspace files."""

import re

from .common import is_ignored

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_files",
        "description": "Search for a regex pattern across files in the workspace. Returns matching lines with file paths and line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for.",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional glob to filter files, e.g. '*.py'. Defaults to all files.",
                },
            },
            "required": ["pattern"],
        },
    },
}


def tool_search_files(args, workspace):
    pattern = args["pattern"]
    glob_pat = args.get("glob", "**/*")
    compiled = re.compile(pattern)
    results = []
    for fpath in workspace.rglob(glob_pat if "*" in glob_pat else f"**/{glob_pat}"):
        if not fpath.is_file():
            continue
        rel = fpath.relative_to(workspace)
        if is_ignored(workspace, rel):
            continue
        try:
            for i, line in enumerate(fpath.read_text(errors="replace").splitlines(), 1):
                if compiled.search(line):
                    results.append(f"{rel}:{i}: {line.rstrip()}")
        except Exception:
            continue
        if len(results) >= 200:
            results.append("... (truncated)")
            break
    return "\n".join(results) if results else "No matches found."
