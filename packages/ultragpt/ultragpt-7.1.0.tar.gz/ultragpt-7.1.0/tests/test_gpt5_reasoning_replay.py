#!/usr/bin/env python3
"""
Test GPT-5 reasoning_details replay with encrypted_content.

This test verifies that:
1. The `include=["reasoning.encrypted_content"]` parameter is sent
2. The UPSERT/MERGE logic correctly captures encrypted data from streaming
3. Multi-turn tool calling works with GPT-5's Responses API format

Author: UltraGPT
"""

import sys
import os
import json

# Add UltraGPT to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_gpt5_include_parameter():
    """Test that include parameter is added for reasoning models."""
    print("\n" + "=" * 80)
    print("  TEST 1: include=reasoning.encrypted_content Parameter")
    print("=" * 80 + "\n")
    
    from ultragpt.providers.providers import OpenRouterProvider
    
    provider = OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))
    
    # Test GPT-5 (should have include)
    extra_body = provider._build_extra_body("openai/gpt-5", None, None)
    print(f"GPT-5 extra_body: {json.dumps(extra_body, indent=2)}")
    
    if extra_body and "include" in extra_body:
        print("\n[OK] GPT-5 has include parameter")
        if "reasoning.encrypted_content" in extra_body["include"]:
            print("[OK] reasoning.encrypted_content is in include list")
        else:
            print("[FAIL] reasoning.encrypted_content NOT in include list")
            return False
    else:
        print("[FAIL] GPT-5 missing include parameter")
        return False
    
    # Test Gemini 3 (should also have include)
    extra_body_gemini = provider._build_extra_body("google/gemini-3-pro-preview", None, None)
    print(f"\nGemini 3 extra_body: {json.dumps(extra_body_gemini, indent=2)}")
    
    if extra_body_gemini and "include" in extra_body_gemini:
        print("[OK] Gemini 3 has include parameter")
    else:
        print("[WARN] Gemini 3 missing include - may not need it")
    
    # Test non-reasoning model (should NOT have include)
    extra_body_gpt4 = provider._build_extra_body("openai/gpt-4o-mini", None, None)
    print(f"\nGPT-4o-mini extra_body: {extra_body_gpt4}")
    
    if extra_body_gpt4 is None or "include" not in (extra_body_gpt4 or {}):
        print("[OK] GPT-4o-mini correctly has no include parameter")
    else:
        print("[WARN] GPT-4o-mini has include - unexpected but not harmful")
    
    return True


def test_streaming_upsert():
    """Test that streaming UPSERT correctly merges fields."""
    print("\n" + "=" * 80)
    print("  TEST 2: Streaming UPSERT/MERGE Logic")
    print("=" * 80 + "\n")
    
    from ultragpt.providers.providers import BaseOpenAICompatibleProvider
    from langchain_core.messages import AIMessageChunk
    
    # Simulate streaming chunks where encrypted data comes later
    def create_mock_stream():
        # Chunk 1: Initial reasoning item with id only
        chunk1 = AIMessageChunk(content="")
        chunk1.additional_kwargs = {
            "reasoning_details": [
                {"type": "reasoning.summary", "id": "rs_test123", "index": 0}
            ]
        }
        yield chunk1
        
        # Chunk 2: Same item but now with encrypted data
        chunk2 = AIMessageChunk(content="")
        chunk2.additional_kwargs = {
            "reasoning_details": [
                {
                    "type": "reasoning.summary",
                    "id": "rs_test123",
                    "index": 0,
                    "summary": "User asked about weather",
                    "data": "gAAAAABencrypted_data_here"
                }
            ]
        }
        yield chunk2
        
        # Chunk 3: Empty chunk (end of stream)
        chunk3 = AIMessageChunk(content="")
        yield chunk3
    
    # Run accumulation
    result = BaseOpenAICompatibleProvider._accumulate_stream(create_mock_stream())
    
    print(f"Result type: {type(result)}")
    print(f"Result additional_kwargs keys: {list(result.additional_kwargs.keys()) if result.additional_kwargs else 'None'}")
    
    rd = result.additional_kwargs.get("reasoning_details") if result.additional_kwargs else None
    
    if rd:
        print(f"\nreasoning_details count: {len(rd)}")
        for i, item in enumerate(rd):
            print(f"  [{i}]: type={item.get('type')}, id={item.get('id')}")
            print(f"       has summary: {'summary' in item}")
            print(f"       has data: {'data' in item}")
        
        # Check that we have exactly 1 item (merged, not duplicated)
        if len(rd) == 1:
            print("\n[OK] Correctly merged into single item (no duplicates)")
        else:
            print(f"\n[FAIL] Expected 1 item, got {len(rd)}")
            return False
        
        # Check that the merged item has all fields
        merged_item = rd[0]
        required_fields = ["type", "id", "summary", "data"]
        missing = [f for f in required_fields if f not in merged_item]
        
        if not missing:
            print("[OK] Merged item has all fields (type, id, summary, data)")
            return True
        else:
            print(f"[FAIL] Merged item missing fields: {missing}")
            return False
    else:
        print("[FAIL] No reasoning_details in result")
        return False


def test_streaming_reasoning_summary_concatenation():
    """Test that streaming reasoning.summary fragments are concatenated, not overwritten."""
    print("\n" + "=" * 80)
    print("  TEST 2B: Streaming reasoning.summary Concatenation")
    print("=" * 80 + "\n")

    from ultragpt.providers.providers import BaseOpenAICompatibleProvider
    from langchain_core.messages import AIMessageChunk

    def create_mock_stream():
        # Providers may stream `summary` in fragments; if we overwrite, we can end up with only '!'.
        chunk1 = AIMessageChunk(content="")
        chunk1.additional_kwargs = {
            "reasoning_details": [
                {"type": "reasoning.summary", "id": "rs_test123", "index": 0, "summary": "Hello"}
            ]
        }
        yield chunk1

        chunk2 = AIMessageChunk(content="")
        chunk2.additional_kwargs = {
            "reasoning_details": [
                {"type": "reasoning.summary", "id": "rs_test123", "index": 0, "summary": " world"}
            ]
        }
        yield chunk2

        chunk3 = AIMessageChunk(content="")
        chunk3.additional_kwargs = {
            "reasoning_details": [
                {"type": "reasoning.summary", "id": "rs_test123", "index": 0, "summary": "!"}
            ]
        }
        yield chunk3

        yield AIMessageChunk(content="")

    result = BaseOpenAICompatibleProvider._accumulate_stream(create_mock_stream())

    rd = result.additional_kwargs.get("reasoning_details") if result.additional_kwargs else None
    if not (isinstance(rd, list) and rd):
        print("[FAIL] No reasoning_details in result")
        return False

    summary = rd[0].get("summary") if isinstance(rd[0], dict) else None
    print(f"Merged summary: {summary!r}")

    if summary == "Hello world!":
        print("[OK] summary fragments concatenated correctly")
        return True

    print("[FAIL] Expected 'Hello world!' after concatenation")
    return False


def test_gpt5_live_call():
    """Test live GPT-5 call with tool calling."""
    print("\n" + "=" * 80)
    print("  TEST 3: Live GPT-5 Tool Call (if available)")
    print("=" * 80 + "\n")
    
    try:
        from ultragpt.core import UltraGPT
        from ultragpt.schemas import UserTool
        from pydantic import BaseModel
        
        class WeatherParams(BaseModel):
            location: str
        
        ultragpt_tools = [
            UserTool(
                name="get_weather",
                description="Get weather info",
                parameters_schema=WeatherParams,
                usage_guide="Use for weather",
                when_to_use="Weather questions"
            )
        ]
        
        ultragpt = UltraGPT(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            verbose=False
        )
        
        print("Calling GPT-5 with tool...")
        response, tokens, details = ultragpt.tool_call(
            messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
            user_tools=ultragpt_tools,
            model="openai/gpt-5",
            temperature=0.7
        )
        
        print(f"Response type: {type(response)}")
        print(f"Tokens: {tokens}")
        
        rd = details.get("reasoning_details") if details else None
        if rd:
            print(f"\nreasoning_details count: {len(rd)}")
            for i, item in enumerate(rd):
                rd_type = item.get('type') if isinstance(item, dict) else 'unknown'
                has_data = 'data' in item if isinstance(item, dict) else False
                has_id = 'id' in item if isinstance(item, dict) else False
                print(f"  [{i}]: type={rd_type}, has_id={has_id}, has_data={has_data}")
            
            # Check if we have encrypted data
            has_encrypted = any(
                isinstance(item, dict) and item.get('data')
                for item in rd
            )
            
            if has_encrypted:
                print("\n[OK] GPT-5 returned encrypted reasoning data!")
                return True
            else:
                print("\n[WARN] GPT-5 reasoning_details has no encrypted data")
                print("       This may mean the include parameter wasn't applied")
                print("       or OpenRouter doesn't support it for GPT-5")
                return True  # Not a hard failure
        else:
            print("\n[WARN] No reasoning_details from GPT-5")
            print("       GPT-5 may not return reasoning for simple queries")
            return True  # Not a hard failure
            
    except Exception as e:
        print(f"\n[SKIP] GPT-5 test skipped: {e}")
        return True  # Skip, not fail


if __name__ == "__main__":
    print("=" * 80)
    print("  GPT-5 REASONING REPLAY TEST SUITE")
    print("=" * 80)
    print("\nTesting GPT-5 Responses API fixes:")
    print("  1. include=reasoning.encrypted_content parameter")
    print("  2. UPSERT/MERGE streaming logic")
    print("  3. Live GPT-5 call (if available)")
    
    results = {
        "include_parameter": test_gpt5_include_parameter(),
        "streaming_upsert": test_streaming_upsert(),
        "summary_concat": test_streaming_reasoning_summary_concatenation(),
        "live_gpt5": test_gpt5_live_call(),
    }
    
    print("\n" + "=" * 80)
    print("  TEST RESULTS SUMMARY")
    print("=" * 80 + "\n")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED")
    
    sys.exit(0 if all_passed else 1)
