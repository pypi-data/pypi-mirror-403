#!/usr/bin/env python3
"""
CrewAI + Ollama + EmoCore Integration
======================================

Run CrewAI agents with EmoCore governance using a local Ollama model.

REQUIREMENTS:
    pip install crewai openai

USAGE:
    # Make sure Ollama is running
    ollama run gemma3:1b
    
    # Run this example
    python integrations/crewai_ollama.py
"""

import sys
import os

# Set Ollama as the backend for CrewAI
os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_MODEL_NAME"] = "gemma3:1b"

try:
    from crewai import Agent, Task, Crew
except ImportError as e:
    print(__doc__)
    print(f"\n[X] Missing dependency: {e}")
    print("\n[+] Install with: pip install crewai")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("[X] OpenAI SDK required")
    print("    pip install openai")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# ============================================================
# EmoCore-Governed CrewAI
# ============================================================

def check_ollama():
    """Verify Ollama is reachable."""
    try:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        print(f"[X] Cannot connect to Ollama: {e}")
        return False

def run_governed_crew():
    print("=" * 60)
    print("CREWAI + OLLAMA + EMOCORE")
    print("=" * 60)
    
    # 1. Check Ollama
    if not check_ollama():
        print("\nMake sure Ollama is running:")
        print("  ollama run gemma3:1b")
        sys.exit(1)
    print(f"[+] Connected to Ollama ({OLLAMA_MODEL})")
    
    # 2. Initialize EmoCore
    emocore_agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 3. Define CrewAI agents
    # Note: CrewAI integration typically requires wrapping the execution
    # This shows the pattern for manual governance integration
    
    researcher = Agent(
        role='Researcher',
        goal='Find information about a topic',
        backstory='You are a thorough researcher.',
        verbose=True,
        allow_delegation=False,
        llm=f"ollama/{OLLAMA_MODEL}"
    )
    
    task = Task(
        description="Summarize what EmoCore does in one sentence.",
        expected_output="A single sentence summary.",
        agent=researcher
    )
    
    print("\n[+] CrewAI Agent configured")
    print(f"    Role: {researcher.role}")
    print(f"    Goal: {researcher.goal}")
    
    # 4. Simulate governance check before/after crew execution
    # In production, you'd hook into CrewAI's callback system
    
    print("\n[Governance Check: Pre-Execution]")
    pre_result = step(emocore_agent, Signals(reward=0.5, novelty=0.8, urgency=0.1))
    print(f"Mode={pre_result.mode.name} | Effort={pre_result.budget.effort:.2f}")
    
    if pre_result.halted:
        print("[!] Pre-execution halt - task would not proceed")
    else:
        print("[+] Governance permits execution")
        print("\n[NOTE] In a real integration, you would now run:")
        print("       crew = Crew(agents=[researcher], tasks=[task])")
        print("       result = crew.kickoff()")
        print("       Then check governance again after execution.")
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_crew()
