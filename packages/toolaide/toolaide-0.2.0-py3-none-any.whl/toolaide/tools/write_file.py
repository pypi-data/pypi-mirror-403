"""Write file tool — writes content to a file in the workspace."""

from .common import _safe_path

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file at the given relative path inside the workspace. Creates parent directories if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file inside the workspace.",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
}


def tool_write_file(args, workspace):
    target = _safe_path(workspace, args["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(args["content"])
    return f"Wrote {len(args['content'])} bytes to {args['path']}"
