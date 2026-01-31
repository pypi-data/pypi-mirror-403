#!/usr/bin/env python3
"""
LangChain + Ollama + EmoCore Integration
=========================================

Run a LangChain agent loop with EmoCore governance using a local Ollama model.

REQUIREMENTS:
    pip install langchain langchain-ollama

USAGE:
    # Make sure Ollama is running with gemma3:1b
    ollama run gemma3:1b
    
    # Run this example
    python integrations/langchain_ollama.py
"""

import sys

# Check dependencies
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as e:
    print(__doc__)
    print(f"\n[X] Missing dependency: {e}")
    print("\n[+] Install with: pip install langchain langchain-ollama")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_BASE_URL = "http://localhost:11434"
MAX_ITERATIONS = 20

# ============================================================
# EmoCore-Governed LangChain Agent
# ============================================================

def run_governed_agent():
    print("=" * 60)
    print("LANGCHAIN + OLLAMA + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize LLM (Ollama)
    try:
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        # Quick connectivity test
        llm.invoke([HumanMessage(content="Say 'ready'")])
        print(f"[+] Connected to Ollama ({OLLAMA_MODEL})")
    except Exception as e:
        print(f"[X] Failed to connect to Ollama: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama run gemma3:1b")
        sys.exit(1)
    
    # 2. Initialize EmoCore
    agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Simulated task loop
    task = "Explain what EmoCore does in one sentence."
    messages = [HumanMessage(content=task)]
    
    for iteration in range(MAX_ITERATIONS):
        print(f"\n[Step {iteration + 1}]")
        
        # Call LLM
        try:
            response = llm.invoke(messages)
            content = response.content
            print(f"LLM: {content[:100]}..." if len(content) > 100 else f"LLM: {content}")
        except Exception as e:
            print(f"LLM Error: {e}")
            content = ""
        
        # Extract signals from LLM response
        # In a real app, you'd analyze the response quality
        has_answer = len(content) > 20
        is_repetitive = iteration > 0 and content == messages[-1].content if isinstance(messages[-1], AIMessage) else False
        
        signals = Signals(
            reward=0.8 if has_answer else 0.1,
            novelty=0.2 if is_repetitive else 0.6,
            urgency=iteration / MAX_ITERATIONS
        )
        
        # 4. EmoCore governance check
        result = step(agent, signals)
        
        print(f"Gov: Mode={result.mode.name} | Effort={result.budget.effort:.2f}")
        
        if result.halted:
            print("\n" + "!" * 60)
            print(f"EMOCORE HALTED: {result.reason}")
            print(f"Failure Type: {result.failure.name}")
            print("!" * 60)
            break
        
        # For this demo, we succeed after first good response
        if has_answer:
            print("\n[OK] Task completed successfully!")
            break
        
        messages.append(AIMessage(content=content))
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_agent()
