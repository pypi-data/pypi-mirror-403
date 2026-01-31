#!/usr/bin/env python3
"""
OpenAI SDK + Ollama + EmoCore Integration
==========================================

Use the OpenAI SDK with Ollama's OpenAI-compatible API, governed by EmoCore.

REQUIREMENTS:
    pip install openai

USAGE:
    # Make sure Ollama is running
    ollama run gemma3:1b
    
    # Run this example
    python integrations/openai_sdk_ollama.py
"""

import sys

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
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MAX_ITERATIONS = 15

# ============================================================
# EmoCore-Governed OpenAI SDK Loop
# ============================================================

def run_governed_loop():
    print("=" * 60)
    print("OPENAI SDK + OLLAMA + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize OpenAI client pointing to Ollama
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama"  # Ollama doesn't need a real key
    )
    
    # Test connection
    try:
        test = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"[+] Connected to Ollama ({OLLAMA_MODEL})")
    except Exception as e:
        print(f"[X] Cannot connect to Ollama: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama run gemma3:1b")
        sys.exit(1)
    
    # 2. Initialize EmoCore
    agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Agentic loop with governance
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
        {"role": "user", "content": "Count from 1 to 5, one number per response."}
    ]
    
    previous_response = ""
    
    for iteration in range(MAX_ITERATIONS):
        print(f"\n[Step {iteration + 1}]")
        
        # Call LLM
        try:
            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=messages,
                max_tokens=50
            )
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            print(f"LLM: {content}")
        except Exception as e:
            print(f"Error: {e}")
            content = ""
            finish_reason = "error"
        
        # Extract signals
        is_complete = "5" in content or finish_reason == "stop"
        is_repetitive = content == previous_response
        made_progress = any(str(i) in content for i in range(1, 6))
        
        signals = Signals(
            reward=0.8 if made_progress else 0.1,
            novelty=0.2 if is_repetitive else 0.6,
            urgency=iteration / MAX_ITERATIONS
        )
        
        # 4. EmoCore governance
        result = step(agent, signals)
        print(f"Gov: Mode={result.mode.name} | Effort={result.budget.effort:.2f}")
        
        if result.halted:
            print("\n" + "!" * 60)
            print(f"EMOCORE HALTED: {result.reason}")
            print(f"Failure Type: {result.failure.name}")
            print("!" * 60)
            break
        
        if is_complete:
            print("\n[OK] Task completed!")
            break
        
        # Continue conversation
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": "Continue"})
        previous_response = content
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_loop()
