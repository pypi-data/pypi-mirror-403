#!/usr/bin/env python3
"""
LangChain + OpenAI + EmoCore Integration
=========================================

Run a LangChain agent with EmoCore governance using the OpenAI API.

REQUIREMENTS:
    pip install langchain langchain-openai

SETUP:
    # Windows PowerShell
    $env:OPENAI_API_KEY = "sk-your-key-here"
    
    # Linux/Mac
    export OPENAI_API_KEY="sk-your-key-here"

USAGE:
    python integrations/langchain_openai.py
"""

import sys
import os

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print(__doc__)
    print("[X] Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as e:
    print(__doc__)
    print(f"\n[X] Missing dependency: {e}")
    print("\n[+] Install with: pip install langchain langchain-openai")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective model
MAX_ITERATIONS = 20

# ============================================================
# EmoCore-Governed LangChain Agent
# ============================================================

def run_governed_agent():
    print("=" * 60)
    print("LANGCHAIN + OPENAI + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize LLM
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    print(f"[+] Connected to OpenAI ({OPENAI_MODEL})")
    
    # 2. Initialize EmoCore
    agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Task loop
    task = "Explain what EmoCore does in one sentence."
    messages = [HumanMessage(content=task)]
    
    for iteration in range(MAX_ITERATIONS):
        print(f"\n[Step {iteration + 1}]")
        
        try:
            response = llm.invoke(messages)
            content = response.content
            print(f"LLM: {content[:100]}..." if len(content) > 100 else f"LLM: {content}")
        except Exception as e:
            print(f"Error: {e}")
            content = ""
        
        # Extract signals
        has_answer = len(content) > 20
        signals = Signals(
            reward=0.8 if has_answer else 0.1,
            novelty=0.6,
            urgency=iteration / MAX_ITERATIONS
        )
        
        # EmoCore check
        result = step(agent, signals)
        print(f"Gov: Mode={result.mode.name} | Effort={result.budget.effort:.2f}")
        
        if result.halted:
            print(f"\n[!] HALTED: {result.reason}")
            break
        
        if has_answer:
            print("\n[OK] Task completed!")
            break
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_agent()
