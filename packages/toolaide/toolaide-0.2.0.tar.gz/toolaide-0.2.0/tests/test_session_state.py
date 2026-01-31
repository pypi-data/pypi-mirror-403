"""Unit tests for SessionState usage tracking."""

from toolaide.cli import SessionState


def test_usage_tracking_across_prompts():
    """Test that context builds up across prompts while per-prompt stats reset."""
    session = SessionState()

    # --- First prompt: 3 API calls with growing context ---
    # Simulates: user prompt -> tool call -> tool call -> final response

    # Call 1: initial prompt
    session.record_usage({"usage": {"prompt_tokens": 1000, "completion_tokens": 200}})
    assert session.calls == 1
    assert session.tokens_used == 1200
    assert session.context_fill == 1000

    # Call 2: after tool result added to context
    session.record_usage({"usage": {"prompt_tokens": 1500, "completion_tokens": 150}})
    assert session.calls == 2
    assert session.tokens_used == 2850  # 1200 + 1650
    assert session.context_fill == 1500

    # Call 3: after another tool result
    session.record_usage({"usage": {"prompt_tokens": 2000, "completion_tokens": 300}})
    assert session.calls == 3
    assert session.tokens_used == 5150  # 2850 + 2300
    assert session.context_fill == 2000

    # --- Reset for second prompt ---
    session.reset_usage()

    # Per-prompt counters reset
    assert session.calls == 0
    assert session.tokens_used == 0
    assert session.last_completion == 0
    # Context fill persists (still 2000, will update on next record)
    assert session.context_fill == 2000

    # --- Second prompt: 1 API call with larger context ---
    # Context grew because conversation history expanded

    session.record_usage({"usage": {"prompt_tokens": 2800, "completion_tokens": 400}})
    assert session.calls == 1
    assert session.tokens_used == 3200
    assert session.context_fill == 2800  # Context grew from 2000 to 2800
    assert session.last_completion == 400


def test_usage_tracking_empty_result():
    """Test handling of missing usage data."""
    session = SessionState()

    session.record_usage({})  # No usage key
    assert session.calls == 1
    assert session.tokens_used == 0
    assert session.context_fill == 0

    session.record_usage({"usage": {}})  # Empty usage
    assert session.calls == 2
    assert session.tokens_used == 0
