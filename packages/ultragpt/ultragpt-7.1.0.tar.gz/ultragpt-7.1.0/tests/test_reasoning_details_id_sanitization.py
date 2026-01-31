#!/usr/bin/env python3
"""Manual test: reasoning_details replay sanitization.

Goal
- When reasoning_details includes encrypted `data`, we MUST strip `id` before sending
  back to the API (store=false cannot resolve rs_... ids).
- When reasoning_details has no `data`, we keep `id` (back-compat).

Run:
  python tests/test_reasoning_details_id_sanitization.py
"""

import os
import sys

# Add UltraGPT to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from langchain_core.messages import AIMessage

# Import applies patches at import-time
import ultragpt.providers  # noqa: F401

from langchain_openai.chat_models import base as lc_base


def _convert(msg: AIMessage) -> dict:
    # API value doesn't matter for this patch; keep explicit.
    return lc_base._convert_message_to_dict(msg, api="chat/completions")


def main() -> int:
    print("=" * 80)
    print("TEST: reasoning_details id stripping when data present")
    print("=" * 80)

    msg_with_data = AIMessage(content="")
    msg_with_data.additional_kwargs = {
        "reasoning_details": [
            {
                "type": "reasoning.summary",
                "id": "rs_should_be_stripped",
                "index": 0,
                "summary": "hello",
                "data": "gAAAAABencrypted",
            }
        ]
    }

    as_dict = _convert(msg_with_data)
    rd = as_dict.get("reasoning_details")

    assert isinstance(rd, list) and len(rd) == 1, f"Unexpected reasoning_details: {rd!r}"
    assert "data" in rd[0] and rd[0]["data"], "Expected encrypted data to be preserved"
    assert "id" not in rd[0], f"Expected id stripped, got: {rd[0]!r}"

    print("[OK] id stripped, data preserved")

    print("\n" + "=" * 80)
    print("TEST: reasoning_details id preserved for non-rs ids when data present")
    print("=" * 80)

    msg_tool_linked_id = AIMessage(content="")
    msg_tool_linked_id.additional_kwargs = {
        "reasoning_details": [
            {
                "type": "reasoning.encrypted",
                "id": "tool_view_sequence_abc123",
                "index": 0,
                "data": "CiQBencrypted",
            }
        ]
    }

    as_dict = _convert(msg_tool_linked_id)
    rd = as_dict.get("reasoning_details")

    assert isinstance(rd, list) and len(rd) == 1, f"Unexpected reasoning_details: {rd!r}"
    assert rd[0].get("data"), "Expected encrypted data to be preserved"
    assert rd[0].get("id") == "tool_view_sequence_abc123", f"Expected id preserved, got: {rd[0]!r}"

    print("[OK] non-rs id preserved")

    print("\n" + "=" * 80)
    print("TEST: reasoning_details id preserved when data absent")
    print("=" * 80)

    msg_no_data = AIMessage(content="")
    msg_no_data.additional_kwargs = {
        "reasoning_details": [
            {
                "type": "reasoning.summary",
                "id": "rs_should_remain",
                "index": 0,
                "summary": "hello",
            }
        ]
    }

    as_dict = _convert(msg_no_data)
    rd = as_dict.get("reasoning_details")

    assert isinstance(rd, list) and len(rd) == 1, f"Unexpected reasoning_details: {rd!r}"
    assert rd[0].get("id") == "rs_should_remain", f"Expected id preserved, got: {rd[0]!r}"

    print("[OK] id preserved")

    print("\nAll good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
