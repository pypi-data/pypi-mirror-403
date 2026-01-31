"""
Tool-calling agent with GLM-4.7-Flash-4bit via mlx-lm.server

Prerequisites:
  Start the server first:
    mlx_lm.server --model mlx-community/GLM-4.7-Flash-4bit --port 8080

Usage:
    toolaide [--workspace /path/to/dir] [--port 8080]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from toolaide.tools import TOOLS, TOOL_DISPATCH

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_FILE = Path("toolaide.log")

logger = logging.getLogger("toolaide")
logger.setLevel(logging.DEBUG)

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_file_handler)


def _log_request_response(request_payload, response_data, elapsed_ms):
    """Log API request and response as pretty-printed JSON."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_ms": elapsed_ms,
        "request": request_payload,
        "response": response_data,
    }
    logger.debug(json.dumps(entry, indent=2, ensure_ascii=False))
    logger.debug("")  # blank line between entries


# ---------------------------------------------------------------------------
# Server communication
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:8080"


def chat(messages, tools=None, base_url=DEFAULT_BASE_URL,
         max_tokens=16384, temperature=0.7, top_p=0.95,
         repetition_penalty=1.0):
    """Send a chat completion request to mlx-lm.server."""
    payload = {
        "model": "mlx-community/GLM-4.7-Flash-4bit",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    start = datetime.now()
    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        json=payload,
        timeout=300,
    )
    elapsed_ms = (datetime.now() - start).total_seconds() * 1000
    resp.raise_for_status()
    response_data = resp.json()

    _log_request_response(payload, response_data, round(elapsed_ms, 1))

    return response_data


# ---------------------------------------------------------------------------
# Session state and slash commands
# ---------------------------------------------------------------------------


class SessionState:
    """Manages runtime session state and slash commands."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        # Per-prompt stats (reset between prompts)
        self.calls = 0           # API calls made during this prompt
        self.tokens_used = 0     # Total tokens across all calls (billing)
        # Session-level stat
        self.context_fill = 0    # Context window usage (latest prompt_tokens)
        # Per-call stat (for verbose output)
        self.last_completion = 0

    def reset_usage(self):
        """Reset per-prompt counters. Context fill persists across session."""
        self.calls = 0
        self.tokens_used = 0
        self.last_completion = 0

    def record_usage(self, result):
        """Record token usage from an API result."""
        usage = result.get("usage", {})
        self.context_fill = usage.get("prompt_tokens", 0)
        self.last_completion = usage.get("completion_tokens", 0)
        self.tokens_used += self.context_fill + self.last_completion
        self.calls += 1

    def report_usage(self, cumulative=False):
        """Print token usage and warn if approaching context limit."""
        pct = self.context_fill / CONTEXT_LIMIT * 100

        if cumulative:
            print(f"\n  [usage] {self.calls} calls, {self.tokens_used} tokens, {pct:.0f}% context")
        else:
            bar_len = 20
            filled = int(bar_len * (self.context_fill / CONTEXT_LIMIT))
            bar = "\u2588" * filled + "\u2591" * (bar_len - filled)

            if self.verbose or pct >= CONTEXT_WARN_THRESHOLD * 100:
                print(f"  [tokens] prompt={self.context_fill} completion={self.last_completion} "
                      f"[{bar}] {pct:.1f}% context")

        # Warnings based on context fill (same for both modes)
        if pct >= 90:
            print("  \u26a0 CRITICAL: Context nearly full! Consider new session.")
        elif pct >= CONTEXT_WARN_THRESHOLD * 100:
            print("  \u26a0 Warning: Context usage high. May need trimming.")

    def handle_command(self, user_input):
        """Handle slash commands. Returns (was_handled, should_continue)."""
        if not user_input.startswith("/"):
            return False, True

        cmd = user_input[1:].strip().lower()
        parts = cmd.split(None, 1)
        cmd_name = parts[0] if parts else ""
        cmd_arg = parts[1] if len(parts) > 1 else None

        if cmd_name in ("v", "verbose"):
            if cmd_arg == "on":
                self.verbose = True
            elif cmd_arg == "off":
                self.verbose = False
            else:
                self.verbose = not self.verbose
            print(f"  [verbose: {'ON' if self.verbose else 'OFF'}]")
            return True, True

        if cmd_name == "help":
            self._print_help()
            return True, True

        if cmd_name in ("quit", "exit", "q"):
            return True, False

        print(f"  [unknown command: /{cmd_name}]")
        return True, True

    def _print_help(self):
        print("  Commands:")
        print("    /verbose, /v       - toggle verbose mode")
        print("    /verbose on|off    - set verbose mode")
        print("    /quit, /exit, /q   - exit the session")
        print("    /help              - show this help")


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

CONTEXT_WARN_THRESHOLD = 0.75
CONTEXT_LIMIT = 128_000  # GLM-4 max context window

# Degenerate output detection
REPEAT_WINDOW = 20  # tokens to check for repetition pattern
MIN_REPEAT_COUNT = 10  # minimum repetitions to consider degenerate


def _detect_degenerate_output(text):
    """Detect and truncate degenerate repetitive output.

    Returns (cleaned_text, was_truncated).
    """
    if len(text) < 200:
        return text, False

    # Look for repeated short patterns (e.g., "9, 9, 9, ...")
    # Check last portion of text for repetition
    check_portion = text[-2000:] if len(text) > 2000 else text

    # Try pattern lengths from 1 to 20 chars
    for pattern_len in range(1, 21):
        if len(check_portion) < pattern_len * MIN_REPEAT_COUNT:
            continue

        # Get the last pattern_len chars as candidate
        candidate = check_portion[-pattern_len:]

        # Count consecutive repetitions from the end
        count = 0
        pos = len(check_portion) - pattern_len
        while pos >= 0 and check_portion[pos:pos + pattern_len] == candidate:
            count += 1
            pos -= pattern_len

        if count >= MIN_REPEAT_COUNT:
            # Found degenerate pattern - find where it started
            repeat_start = len(check_portion) - (count * pattern_len)
            # Map back to original text position
            if len(text) > 2000:
                repeat_start = len(text) - 2000 + repeat_start
            return text[:repeat_start].rstrip() + "\n... [truncated: degenerate repetition detected]", True

    return text, False


def run_agent_loop(user_input, messages, tools, workspace, base_url, session):
    """Run a single turn: send user message, handle any tool calls, repeat until text reply."""
    session.reset_usage()
    messages.append({"role": "user", "content": user_input})

    last_call_sig = None
    repeat_count = 0
    MAX_REPEATS = 3

    while True:
        try:
            result = chat(messages, tools=tools, base_url=base_url)
        except KeyboardInterrupt:
            print("\n  [cancelled by user]")
            messages.pop()
            return
        except requests.exceptions.ReadTimeout:
            print("\n  [request timed out]")
            messages.pop()
            return
        except requests.exceptions.RequestException as e:
            print(f"\n  [request failed: {e}]")
            messages.pop()
            return

        session.record_usage(result)
        session.report_usage(cumulative=False)

        choice = result["choices"][0]
        msg = choice["message"]

        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            # Final text response
            content = msg.get("content", "(no content)")
            content, was_truncated = _detect_degenerate_output(content)

            if was_truncated:
                # Update the message in history with cleaned content
                messages[-1] = {**msg, "content": content}
                print("  [warning] Degenerate repetition detected and truncated")
            print(f"\n{content}")
            session.report_usage(cumulative=True)
            print()
            return

        # Detect repetition loops
        call_sig = json.dumps(
            [(tc["function"]["name"], tc["function"]["arguments"]) for tc in tool_calls],
            sort_keys=True,
        )
        if call_sig == last_call_sig:
            repeat_count += 1
            if repeat_count >= MAX_REPEATS:
                print(f"\n  [loop detected: same tool call repeated {MAX_REPEATS} times, breaking out]\n")
                return
        else:
            repeat_count = 0
            last_call_sig = call_sig

        # Not final, calling tools - output reasoning and intermediate content
        if session.verbose and msg.get("reasoning"):
            print(f"  [reasoning] {msg['reasoning']}")
        if msg.get("content"):
            print(f"\n{msg['content']}\n")

        # Execute each tool call
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}

            print(f"  [tool] {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

            handler = TOOL_DISPATCH.get(fn_name)
            if handler is None:
                result_str = f"Error: unknown tool '{fn_name}'"
            else:
                try:
                    result_str = handler(fn_args, workspace)
                except Exception as e:
                    result_str = f"Error: {e}"

            if session.verbose:
                print(f"  [result] {result_str[:200]}{'...' if len(result_str) > 200 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })


def main():
    parser = argparse.ArgumentParser(description="Tool-calling agent with GLM-4.7-Flash-4bit")
    parser.add_argument("--workspace", type=str, default=".",
                        help="Workspace directory the tools operate in")
    parser.add_argument("--port", type=int, default=8080,
                        help="mlx-lm.server port")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show reasoning and tool results")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    base_url = f"http://localhost:{args.port}"
    state = SessionState(verbose=args.verbose)

    print(f"Workspace : {workspace}")
    print(f"Server    : {base_url}")
    print(f"Tools     : {[t['function']['name'] for t in TOOLS]}")
    print("Type /help for commands, /quit to exit.\n")

    system_msg = (
        "You are a helpful coding assistant with access to workspace tools.\n\n"
        "IMPORTANT RULES:\n"
        "1. Before writing a file, ALWAYS read it first to see its current contents.\n"
        "2. When modifying a file, apply ONLY the requested change. Keep everything else exactly as-is.\n"
        "3. After writing, verify the result by reading the file back.\n"
        "4. Double-check that the content you pass to write_file actually reflects the change requested.\n"
        "5. Never call the same tool with the same arguments twice in a row.\n\n"
        f"The workspace root is: {workspace}"
    )
    messages = [{"role": "system", "content": system_msg}]

    while True:
        try:
            user_input = input(" > ").strip()
            print()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue

        handled, should_continue = state.handle_command(user_input)
        if handled:
            if should_continue:
                continue
            else:
                break

        run_agent_loop(user_input, messages, TOOLS, workspace, base_url, state)


if __name__ == "__main__":
    main()
