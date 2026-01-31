#!/usr/bin/env python3
"""
OpenAI SDK + EmoCore Integration
=================================

Use the OpenAI SDK directly with EmoCore governance.

REQUIREMENTS:
    pip install openai

SETUP:
    # Windows PowerShell
    $env:OPENAI_API_KEY = "sk-your-key-here"
    
    # Linux/Mac
    export OPENAI_API_KEY="sk-your-key-here"

USAGE:
    python integrations/openai_sdk.py
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
MAX_ITERATIONS = 15

# ============================================================
# EmoCore-Governed OpenAI Loop
# ============================================================

def run_governed_loop():
    print("=" * 60)
    print("OPENAI SDK + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize client
    client = OpenAI()
    print(f"[+] Connected to OpenAI ({OPENAI_MODEL})")
    
    # 2. Initialize EmoCore
    agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Agentic loop
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count from 1 to 5, one number per response."}
    ]
    
    previous_response = ""
    
    for iteration in range(MAX_ITERATIONS):
        print(f"\n[Step {iteration + 1}]")
        
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=50
            )
            content = response.choices[0].message.content
            print(f"LLM: {content}")
        except Exception as e:
            print(f"Error: {e}")
            content = ""
        
        # Extract signals
        is_complete = "5" in content
        is_repetitive = content == previous_response
        made_progress = any(str(i) in content for i in range(1, 6))
        
        signals = Signals(
            reward=0.8 if made_progress else 0.1,
            novelty=0.2 if is_repetitive else 0.6,
            urgency=iteration / MAX_ITERATIONS
        )
        
        # EmoCore check
        result = step(agent, signals)
        print(f"Gov: Mode={result.mode.name} | Effort={result.budget.effort:.2f}")
        
        if result.halted:
            print(f"\n[!] HALTED: {result.reason}")
            break
        
        if is_complete:
            print("\n[OK] Task completed!")
            break
        
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": "Continue"})
        previous_response = content
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_loop()
