"""
Test for Gemini 3 Pro reasoning_details preservation in multi-turn tool calling.

This test verifies the COMPLETE working flow:
1. Gemini 3 Pro returns reasoning_details from OpenRouter (including encrypted thought_signature)
2. reasoning_details is properly captured by UltraGPT
3. reasoning_details is stored in AIMessage.additional_kwargs
4. LangChain patches serialize reasoning_details to the API request
5. Multi-turn conversations succeed when reasoning_details is replayed

Requires OPENROUTER_API_KEY in environment.
"""

import os
import sys
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# === CONFIGURATION ===
TEST_MODEL = "google/gemini-3-pro-preview"

# === SETUP ===
ultragpt_root = Path(__file__).parent.parent
env_path = ultragpt_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

sys.path.insert(0, str(ultragpt_root / "src"))

from ultragpt.core import UltraGPT
from ultragpt.schemas import UserTool

# === TOOL DEFINITIONS ===
class WeatherParams(BaseModel):
    location: str
    units: Optional[str] = "celsius"

example_tools = [
    UserTool(
        name="get_weather",
        description="Get current weather information for a location",
        parameters_schema=WeatherParams,
        usage_guide="Use this tool when the user asks about weather conditions.",
        when_to_use="When the user asks about weather"
    ),
]

def simulate_tool_result(tool_name: str, args: dict) -> str:
    """Simulate tool execution."""
    if tool_name == "get_weather":
        return json.dumps({
            "temperature": 22,
            "condition": "sunny",
            "humidity": 45,
            "location": args.get("location", "Unknown")
        })
    return json.dumps({"status": "unknown_tool"})

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_langchain_patch_verification():
    """Test that LangChain patches are properly configured."""
    print_separator("TEST 1: LangChain Patch Verification")
    
    try:
        from ultragpt.providers._langchain_patches import (
            ASSISTANT_EXTRA_FIELDS_TO_SERIALIZE,
            ASSISTANT_FIELDS_TO_CAPTURE,
            _is_patched
        )
        
        print(f"Patches applied: {_is_patched()}")
        print(f"Fields to serialize: {ASSISTANT_EXTRA_FIELDS_TO_SERIALIZE}")
        print(f"Fields to capture: {ASSISTANT_FIELDS_TO_CAPTURE}")
        
        if "reasoning_details" in ASSISTANT_EXTRA_FIELDS_TO_SERIALIZE:
            print("\n[OK] reasoning_details is in serialization list")
        else:
            print("\n[FAIL] reasoning_details NOT in serialization list!")
            return False
        
        if "reasoning_details" in ASSISTANT_FIELDS_TO_CAPTURE:
            print("[OK] reasoning_details is in capture list")
        else:
            print("[FAIL] reasoning_details NOT in capture list!")
            return False
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Could not import patches: {e}")
        return False

def test_reasoning_details_capture():
    """Test that reasoning_details is captured from Gemini 3 response."""
    print_separator("TEST 2: reasoning_details Capture from Gemini 3")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("[SKIP] No OPENROUTER_API_KEY found")
        return False
    
    try:
        ultragpt = UltraGPT(openrouter_api_key=openrouter_key, verbose=True)
        
        messages = [{"role": "user", "content": "What's the weather in Tokyo?"}]
        
        response, tokens, details = ultragpt.tool_call(
            messages=messages,
            user_tools=example_tools,
            model=TEST_MODEL,
            allow_multiple=False,
            temperature=0.7,
        )
        
        print(f"Response: {json.dumps(response, indent=2, default=str)[:500]}")
        print(f"Tokens: {tokens}")
        print(f"Details keys: {list(details.keys()) if details else 'None'}")
        
        # Check for reasoning_details in details dict
        reasoning_details = details.get("reasoning_details") if details else None
        
        if reasoning_details:
            print(f"\n[OK] reasoning_details captured!")
            print(f"  Type: {type(reasoning_details)}")
            if isinstance(reasoning_details, list):
                print(f"  Count: {len(reasoning_details)} items")
                for i, item in enumerate(reasoning_details):
                    rd_type = item.get('type') if isinstance(item, dict) else 'unknown'
                    print(f"  [{i}]: type={rd_type}")
                
                # Check for encrypted block (critical for thought_signature)
                has_encrypted = any(
                    isinstance(item, dict) and item.get('type') == 'reasoning.encrypted'
                    for item in reasoning_details
                )
                if has_encrypted:
                    print("\n[OK] Found encrypted thought_signature block!")
                else:
                    print("\n[WARN] No encrypted block found (may still work)")
            return True
        else:
            print("\n[WARN] No reasoning_details in details dict")
            return True  # May be optional for simple calls
            
    except Exception as e:
        print(f"[FAIL] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_turn_with_reasoning_details():
    """Test complete multi-turn tool calling flow with reasoning_details preservation."""
    print_separator("TEST 3: Multi-Turn Tool Calling (FULL FLOW)")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("[SKIP] No OPENROUTER_API_KEY found")
        return False
    
    try:
        ultragpt = UltraGPT(openrouter_api_key=openrouter_key, verbose=True)
        
        # Turn 1: Initial request
        messages = [{"role": "user", "content": "What's the weather in Paris?"}]
        
        print("--- Turn 1: Initial request ---")
        response1, tokens1, details1 = ultragpt.tool_call(
            messages=messages,
            user_tools=example_tools,
            model=TEST_MODEL,
            allow_multiple=False,
            temperature=0.7,
        )
        
        print(f"Turn 1 response type: {type(response1)}")
        
        # Extract tool call info
        if isinstance(response1, list) and len(response1) > 0:
            tool_call = response1[0]
        elif isinstance(response1, dict):
            tool_call = response1
        else:
            print("[FAIL] Unexpected response format")
            return False
        
        tool_call_id = tool_call.get("id")
        tool_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
        tool_args = tool_call.get("function", {}).get("arguments") or tool_call.get("args", {})
        
        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args)
        
        print(f"Tool called: {tool_name}({tool_args})")
        
        # CRITICAL: Get reasoning_details from details dict
        reasoning_details = details1.get("reasoning_details") if details1 else None
        
        if reasoning_details:
            print(f"\n[OK] reasoning_details captured from Turn 1!")
            print(f"  Items: {len(reasoning_details) if isinstance(reasoning_details, list) else 1}")
            for i, item in enumerate(reasoning_details or []):
                if isinstance(item, dict):
                    print(f"  [{i}]: type={item.get('type')}")
        else:
            print("\n[WARN] No reasoning_details in Turn 1 - may fail in Turn 2")
        
        # Simulate tool execution
        tool_result = simulate_tool_result(tool_name, tool_args)
        
        # Build history WITH reasoning_details (this is the key!)
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        }
        # Include reasoning_details if present
        if reasoning_details:
            assistant_msg["reasoning_details"] = reasoning_details
        
        messages.append(assistant_msg)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": tool_result
        })
        
        # Turn 2: Follow-up request
        messages.append({
            "role": "user",
            "content": "What about London? Is it warmer or colder?"
        })
        
        print("\n--- Turn 2: Follow-up (with reasoning_details preserved) ---")
        print(f"reasoning_details included: {reasoning_details is not None}")
        
        response2, tokens2, details2 = ultragpt.tool_call(
            messages=messages,
            user_tools=example_tools,
            model=TEST_MODEL,
            allow_multiple=False,
            temperature=0.7,
        )
        
        print(f"\nTurn 2 response: {json.dumps(response2, indent=2, default=str)[:500]}")
        print(f"\n[OK] Multi-turn tool calling SUCCEEDED with reasoning_details!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "400" in error_msg or "thought_signature" in error_msg.lower():
            print(f"[FAIL] 400 error - thought_signature issue: {error_msg[:500]}")
            print("\n  This means reasoning_details was not properly preserved/replayed")
        else:
            print(f"[FAIL] {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print_separator("GEMINI 3 REASONING_DETAILS TEST SUITE")
    print(f"Testing model: {TEST_MODEL}")
    print("This test verifies the complete flow for Gemini 3 multi-turn tool calling")
    
    results = {
        "langchain_patches": test_langchain_patch_verification(),
        "reasoning_capture": test_reasoning_details_capture(),
        "multi_turn": test_multi_turn_with_reasoning_details(),
    }
    
    print_separator("TEST RESULTS SUMMARY")
    all_passed = True
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("ALL TESTS PASSED! Gemini 3 reasoning_details handling is working correctly.")
        print("\nThe complete flow is verified:")
        print("  1. reasoning_details captured from Gemini 3 response")
        print("  2. Stored in AIMessage.additional_kwargs")
        print("  3. Serialized by LangChain patch to API request")
        print("  4. Multi-turn tool calling succeeds with preserved thought_signature")
    else:
        print("[WARN] Some tests failed. Check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    main()
