"""
Manual test for GPT-5.2 ::high alias reasoning_details preservation across tool-call turns.

Run:
  python tests/test_reasoning_high_alias.py

Requires OPENROUTER_API_KEY in UltraGPT/.env (OPENAI_API_KEY fallback supported).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

# === SETUP ===
ultragpt_root = Path(__file__).parent.parent
env_path = ultragpt_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

sys.path.insert(0, str(ultragpt_root / "src"))

from ultragpt.core import UltraGPT
from ultragpt.schemas import UserTool


class SumParams(BaseModel):
    a: float
    b: float


example_tools = [
    UserTool(
        name="sum_numbers",
        description="Add two numbers and return the sum.",
        parameters_schema=SumParams,
        usage_guide="Use when the user asks to add numbers.",
        when_to_use="When asked to compute a sum.",
    ),
]


def simulate_tool_result(args: dict) -> str:
    return json.dumps({"result": args.get("a", 0) + args.get("b", 0)})


def _print_reasoning_details(reasoning_details) -> None:
    if not reasoning_details:
        print("No reasoning_details found on response.")
        return

    print(f"reasoning_details count: {len(reasoning_details)}")
    if len(reasoning_details) < 2:
        print("WARN: Expected multiple reasoning blocks; got fewer than 2.")

    for idx, item in enumerate(reasoning_details, 1):
        if isinstance(item, dict):
            print(f"  [{idx}] type={item.get('type')} id={item.get('id')} format={item.get('format')}")
        else:
            print(f"  [{idx}] {item}")


def main() -> int:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY (or OPENAI_API_KEY) not found in UltraGPT/.env")
        return 1

    model = os.getenv("OPENROUTER_REASONING_TEST_MODEL", "openai/gpt-5.2::high")

    ultragpt = UltraGPT(openrouter_api_key=api_key, verbose=True)
    _, normalized_model, deepthink_forced = ultragpt.provider_manager._normalize_model_for_request(model, None)
    print(f"Normalized model: {normalized_model} | deepthink forced: {deepthink_forced}")

    messages = [{"role": "user", "content": "How many Rs are in Strawberry rarry berry in my cherry? Think carefully."}]

    print("\n=== Turn 1 ===")
    response, tokens, details = ultragpt.tool_call(
        messages=messages,
        user_tools=example_tools,
        model=model,
        allow_multiple=False,
        temperature=0.2,
        max_tokens=2048,
    )

    # Extract tool call
    if isinstance(response, list) and response:
        tool_call = response[0]
    elif isinstance(response, dict):
        tool_call = response
    else:
        print("ERROR: Unexpected tool_call response format.")
        return 2

    tool_call_id = tool_call.get("id")
    tool_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
    tool_args = tool_call.get("function", {}).get("arguments") or tool_call.get("args", {})
    if isinstance(tool_args, str):
        tool_args = json.loads(tool_args)

    reasoning_details = details.get("reasoning_details") if details else None
    _print_reasoning_details(reasoning_details)
    print(
        "Reasoning tokens (API):",
        details.get("reasoning_tokens") if details else None,
        "| Reasoning text present:",
        bool(details.get("reasoning_text")) if details else False,
    )

    tool_result = simulate_tool_result(tool_args)

    # Build history WITH reasoning_details
    assistant_msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": [tool_call],
    }
    if reasoning_details:
        assistant_msg["reasoning_details"] = reasoning_details

    messages.append(assistant_msg)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": tool_result,
    })
    messages.append({"role": "user", "content": "Answer in one sentence."})

    print("\n=== Turn 2 ===")
    final_text, final_tokens, final_details = ultragpt.chat(
        messages=messages,
        model=model,
        temperature=0.2,
        max_tokens=1024,
    )

    print(f"Final response: {final_text}")
    _print_reasoning_details(final_details.get("reasoning_details"))
    print(
        "Reasoning tokens (API):",
        final_details.get("reasoning_tokens"),
        "| Reasoning text present:",
        bool(final_details.get("reasoning_text")),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
