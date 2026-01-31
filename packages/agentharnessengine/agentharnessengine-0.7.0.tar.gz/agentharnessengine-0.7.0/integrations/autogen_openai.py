#!/usr/bin/env python3
"""
AutoGen + OpenAI + EmoCore Integration
=======================================

Run AutoGen multi-agent conversation with EmoCore governance using OpenAI.

REQUIREMENTS:
    pip install autogen-agentchat autogen-ext-models-openai

SETUP:
    # Windows PowerShell
    $env:OPENAI_API_KEY = "sk-your-key-here"
    
    # Linux/Mac
    export OPENAI_API_KEY="sk-your-key-here"

USAGE:
    python integrations/autogen_openai.py
"""

import sys
import os

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print(__doc__)
    print("[X] Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError as e:
    print(__doc__)
    print(f"\n[X] Missing dependency: {e}")
    print("\n[+] Install with: pip install openai")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OPENAI_MODEL = "gpt-4o-mini"
MAX_ROUNDS = 10

# ============================================================
# EmoCore-Governed AutoGen Chat
# ============================================================

def run_governed_autogen():
    print("=" * 60)
    print("AUTOGEN + OPENAI + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize OpenAI client
    client = OpenAI()
    print(f"[+] Connected to OpenAI ({OPENAI_MODEL})")
    
    # 2. Initialize EmoCore
    emocore_agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Simulated multi-agent conversation
    conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    for round_num in range(MAX_ROUNDS):
        print(f"\n[Round {round_num + 1}]")
        
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=conversation,
                max_tokens=100
            )
            content = response.choices[0].message.content
            print(f"Agent: {content}")
        except Exception as e:
            print(f"Error: {e}")
            content = ""
        
        # Extract signals
        has_answer = "Paris" in content or len(content) > 10
        signals = Signals(
            reward=0.9 if has_answer else 0.2,
            novelty=0.5,
            urgency=round_num / MAX_ROUNDS
        )
        
        # EmoCore check
        result = step(emocore_agent, signals)
        print(f"Gov: Mode={result.mode.name} | Effort={result.budget.effort:.2f}")
        
        if result.halted:
            print(f"\n[!] HALTED: {result.reason}")
            break
        
        if has_answer:
            print("\n[OK] Conversation completed!")
            break
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_autogen()
