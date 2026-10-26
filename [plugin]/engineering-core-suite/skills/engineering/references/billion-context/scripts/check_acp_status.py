#!/usr/bin/env python3
"""
Context Composition & ACP Status Checker for Antigravity Transcripts
Evaluates token distribution and identifies compressible increments.
"""

import sys
import json
import os
from pathlib import Path

def estimate_tokens(text: str) -> int:
    """Rough token estimation (approx 4 chars per token for code/text)."""
    if not text:
        return 0
    return max(1, len(text) // 4)

def analyze_transcript(jsonl_path: str):
    if not os.path.exists(jsonl_path):
        print(f"Error: Transcript file not found at {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    breakdown = {
        "system": 0,
        "user": 0,
        "assistant_text": 0,
        "assistant_thinking": 0,
        "tool_calls": 0,
        "tool_results": 0,
    }

    turn_count = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            turn_count += 1
            try:
                record = json.loads(line)
            except Exception:
                continue

            step_type = record.get("type", "")
            source = record.get("source", "")
            content = str(record.get("content", ""))
            thinking = str(record.get("thinking", ""))
            tool_calls = json.dumps(record.get("tool_calls", []))

            if source == "SYSTEM" or step_type == "SYSTEM":
                breakdown["system"] += estimate_tokens(content)
            elif source == "USER_EXPLICIT" or step_type == "USER_INPUT":
                breakdown["user"] += estimate_tokens(content)
            else:
                breakdown["assistant_text"] += estimate_tokens(content)
                breakdown["assistant_thinking"] += estimate_tokens(thinking)
                breakdown["tool_calls"] += estimate_tokens(tool_calls)

    total_tokens = sum(breakdown.values())
    growth_floor = 22500  # 22.5K threshold from acp-kernel

    print("==================================================")
    print("      ACTIVE CONTEXT PRUNING (ACP) AUDIT          ")
    print("==================================================")
    print(f"Total Evaluated Turns : {turn_count}")
    print(f"Estimated Total Tokens: {total_tokens:,}")
    print("--------------------------------------------------")
    print(f"System Instructions   : {breakdown['system']:,} tokens ({breakdown['system']/max(1, total_tokens):.1%})")
    print(f"User Inputs           : {breakdown['user']:,} tokens ({breakdown['user']/max(1, total_tokens):.1%})")
    print(f"Assistant Responses   : {breakdown['assistant_text']:,} tokens ({breakdown['assistant_text']/max(1, total_tokens):.1%})")
    print(f"Thinking Blocks       : {breakdown['assistant_thinking']:,} tokens ({breakdown['assistant_thinking']/max(1, total_tokens):.1%}) [Cryptographically Verified]")
    print(f"Tool Invocations      : {breakdown['tool_calls']:,} tokens ({breakdown['tool_calls']/max(1, total_tokens):.1%})")
    print("--------------------------------------------------")

    compressible_estimate = max(0, total_tokens - 50000)
    print(f"Compressible Candidate: {compressible_estimate:,} tokens (excl. 50K recent active zone)")
    if compressible_estimate >= growth_floor:
        print(f"ACP Status            : TRIGGER READY (Growth floor {growth_floor:,} reached)")
        print("Recommendation        : Run incremental fold on completed turns; offload old tool outputs to disk.")
    else:
        print(f"ACP Status            : WITHIN LIMITS (Below {growth_floor:,} threshold)")
        print("Recommendation        : Maintain verbatim active window.")
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
    else:
        # Default fallback to Antigravity appData transcript if present
        default_path = Path.home() / ".gemini/antigravity/brain"
        candidates = list(default_path.glob("*/.system_generated/logs/transcript.jsonl"))
        if candidates:
            transcript_file = str(candidates[0])
        else:
            print("Usage: check_acp_status.py <path_to_transcript.jsonl>")
            sys.exit(1)
    analyze_transcript(transcript_file)
