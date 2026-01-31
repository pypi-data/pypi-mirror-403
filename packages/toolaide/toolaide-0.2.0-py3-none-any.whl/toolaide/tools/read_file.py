"""Read file tool — reads file contents from the workspace."""

from .common import _safe_path

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file at the given relative path inside the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file inside the workspace.",
                }
            },
            "required": ["path"],
        },
    },
}


def tool_read_file(args, workspace):
    target = _safe_path(workspace, args["path"])
    if not target.is_file():
        return f"Error: {args['path']} is not a file."
    content = target.read_text(errors="replace")
    if len(content) > 50_000:
        content = content[:50_000] + "\n... (truncated)"
    return content
