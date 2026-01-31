#!/usr/bin/env python3
"""
AutoGen + Ollama + EmoCore Integration
=======================================

Run AutoGen multi-agent conversation with EmoCore governance using Ollama.

REQUIREMENTS:
    pip install autogen-agentchat autogen-ext openai

USAGE:
    # Make sure Ollama is running
    ollama run gemma3:1b
    
    # Run this example
    python integrations/autogen_ollama.py
"""

import sys
import asyncio

# Check dependencies
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_agentchat.teams import RoundRobinGroupChat
except ImportError:
    try:
        # Try legacy API
        import autogen
        print("[!] Using legacy AutoGen API")
    except ImportError as e:
        print(__doc__)
        print(f"\n[X] Missing dependency: {e}")
        print("\n[+] Install with: pip install autogen-agentchat autogen-ext")
        sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("[X] OpenAI SDK required for Ollama backend")
    print("    pip install openai")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MAX_ROUNDS = 10

# ============================================================
# EmoCore-Governed AutoGen Chat
# ============================================================

def check_ollama_connection():
    """Verify Ollama is reachable."""
    try:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Say ready"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        print(f"[X] Cannot connect to Ollama: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama run gemma3:1b")
        return False

def run_governed_autogen():
    print("=" * 60)
    print("AUTOGEN + OLLAMA + EMOCORE")
    print("=" * 60)
    
    # 1. Check Ollama
    if not check_ollama_connection():
        sys.exit(1)
    print(f"[+] Connected to Ollama ({OLLAMA_MODEL})")
    
    # 2. Initialize EmoCore
    emocore_agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Simulate multi-turn conversation with governance
    # Note: Full AutoGen integration requires deeper hooks into the conversation loop
    # This demonstrates the pattern for manual integration
    
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "What is 2+2?"}
    ]
    
    for round_num in range(MAX_ROUNDS):
        print(f"\n[Round {round_num + 1}]")
        
        # Get LLM response
        try:
            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=conversation,
                max_tokens=100
            )
            content = response.choices[0].message.content
            print(f"Agent: {content}")
        except Exception as e:
            print(f"Error: {e}")
            content = ""
        
        # Extract signals
        has_answer = "4" in content or len(content) > 10
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
            print("\n[OK] Conversation completed successfully!")
            break
        
        conversation.append({"role": "assistant", "content": content})
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_autogen()
