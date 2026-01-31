"""List files tool — lists directory contents in the workspace."""

from .common import _safe_path, is_ignored

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files and directories at the given relative path inside the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path inside the workspace. Use '.' for the root.",
                }
            },
            "required": ["path"],
        },
    },
}


def tool_list_files(args, workspace):
    target = _safe_path(workspace, args.get("path", "."))
    if not target.is_dir():
        return f"Error: {args['path']} is not a directory."
    entries = sorted(target.iterdir())
    lines = []
    for e in entries:
        rel = e.relative_to(workspace)
        if is_ignored(workspace, rel):
            continue
        prefix = "d " if e.is_dir() else "f "
        lines.append(prefix + e.name)
    return "\n".join(lines) if lines else "(empty directory)"
