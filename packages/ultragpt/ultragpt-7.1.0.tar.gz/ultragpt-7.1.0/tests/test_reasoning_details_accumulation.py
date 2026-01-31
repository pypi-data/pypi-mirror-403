#!/usr/bin/env python3
"""Manual tests: reasoning_details accumulation for streaming.

Run:
  python tests/test_reasoning_details_accumulation.py
"""

import os
import sys

# Add UltraGPT to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from langchain_core.messages import AIMessageChunk

from ultragpt.providers.providers import BaseOpenAICompatibleProvider


def _chunk(reasoning_details=None) -> AIMessageChunk:
    additional = {}
    if reasoning_details is not None:
        additional["reasoning_details"] = reasoning_details
    return AIMessageChunk(content="", additional_kwargs=additional)


def _accumulate(chunks):
    return BaseOpenAICompatibleProvider._accumulate_stream(iter(chunks))


def _rd(message):
    return getattr(message, "additional_kwargs", {}).get("reasoning_details")


def _assert_list_len(items, expected):
    assert isinstance(items, list), f"Expected list, got {type(items)!r}"
    assert len(items) == expected, f"Expected {expected} items, got {len(items)}"


def main() -> int:
    print("=" * 80)
    print("TEST: multiple unkeyed blocks in same chunk stay distinct")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk(
                [
                    {"type": "reasoning.summary", "summary": "A"},
                    {"type": "reasoning.summary", "summary": "B"},
                ]
            )
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 2)
    assert items[0]["summary"] == "A"
    assert items[1]["summary"] == "B"
    print("[OK] distinct unkeyed blocks preserved")

    print("\n" + "=" * 80)
    print("TEST: unkeyed streaming merge across chunks")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk([{"type": "reasoning.summary", "summary": "Hello"}]),
            _chunk([{"type": "reasoning.summary", "summary": "Hello, world"}]),
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 1)
    assert items[0]["summary"] == "Hello, world"
    print("[OK] unkeyed stream fragments merged")

    print("\n" + "=" * 80)
    print("TEST: late id merges into unkeyed item")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk([{"type": "reasoning.summary", "summary": "Hi"}]),
            _chunk([{"type": "reasoning.summary", "summary": "Hi!", "id": "rs_1"}]),
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 1)
    assert items[0]["summary"] == "Hi!"
    assert items[0]["id"] == "rs_1"
    print("[OK] late id merged and preserved")

    print("\n" + "=" * 80)
    print("TEST: late index merges into unkeyed item")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk([{"type": "reasoning.summary", "summary": "Seed"}]),
            _chunk([{"type": "reasoning.summary", "summary": "Seed+", "index": 0}]),
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 1)
    assert items[0]["summary"] == "Seed+"
    assert items[0]["index"] == 0
    print("[OK] late index merged and preserved")

    print("\n" + "=" * 80)
    print("TEST: index merge with id alias")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk([{"type": "reasoning.summary", "summary": "Start", "index": 0}]),
            _chunk(
                [
                    {
                        "type": "reasoning.summary",
                        "summary": "Start plus",
                        "index": 0,
                        "id": "rs_x",
                    }
                ]
            ),
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 1)
    assert items[0]["summary"] == "Start plus"
    assert items[0]["id"] == "rs_x"
    print("[OK] index-based merge with late id")

    print("\n" + "=" * 80)
    print("TEST: same index different types stay distinct")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk(
                [
                    {"type": "reasoning.summary", "summary": "S", "index": 0},
                    {"type": "reasoning.encrypted", "data": "abc", "index": 0},
                ]
            )
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 2)
    assert items[0]["type"] != items[1]["type"]
    print("[OK] multiple types with same index preserved")

    print("\n" + "=" * 80)
    print("TEST: indexed + unkeyed same type stay distinct")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk(
                [
                    {"type": "reasoning.summary", "summary": "Indexed", "index": 0},
                    {"type": "reasoning.summary", "summary": "Unkeyed"},
                ]
            )
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 2)
    print("[OK] indexed and unkeyed blocks preserved")

    print("\n" + "=" * 80)
    print("TEST: text field merges across chunks")
    print("=" * 80)
    msg = _accumulate(
        [
            _chunk([{"type": "reasoning.text", "text": "A"}]),
            _chunk([{"type": "reasoning.text", "text": "AB"}]),
        ]
    )
    items = _rd(msg)
    _assert_list_len(items, 1)
    assert items[0]["text"] == "AB"
    print("[OK] streamed text merged")

    print("\nAll good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
