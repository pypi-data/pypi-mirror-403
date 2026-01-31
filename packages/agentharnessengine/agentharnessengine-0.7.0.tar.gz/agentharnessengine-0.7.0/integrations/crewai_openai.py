#!/usr/bin/env python3
"""
CrewAI + OpenAI + EmoCore Integration
======================================

Run CrewAI agents with EmoCore governance using the OpenAI API.

REQUIREMENTS:
    pip install crewai

SETUP:
    # Windows PowerShell
    $env:OPENAI_API_KEY = "sk-your-key-here"
    
    # Linux/Mac
    export OPENAI_API_KEY="sk-your-key-here"

USAGE:
    python integrations/crewai_openai.py
"""

import sys
import os

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print(__doc__)
    print("[X] Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

try:
    from crewai import Agent, Task, Crew
except ImportError as e:
    print(__doc__)
    print(f"\n[X] Missing dependency: {e}")
    print("\n[+] Install with: pip install crewai")
    sys.exit(1)

from governance import EmoCoreAgent, step, Signals

# ============================================================
# Configuration
# ============================================================
OPENAI_MODEL = "gpt-4o-mini"

# ============================================================
# EmoCore-Governed CrewAI
# ============================================================

def run_governed_crew():
    print("=" * 60)
    print("CREWAI + OPENAI + EMOCORE")
    print("=" * 60)
    
    # 1. Initialize EmoCore
    emocore_agent = EmoCoreAgent()
    print("[+] EmoCore governance initialized")
    print("-" * 60)
    
    # 2. Define CrewAI agents
    researcher = Agent(
        role='Researcher',
        goal='Find information about a topic',
        backstory='You are a thorough researcher.',
        verbose=True,
        allow_delegation=False,
        llm=OPENAI_MODEL
    )
    
    task = Task(
        description="Summarize what EmoCore does in one sentence.",
        expected_output="A single sentence summary.",
        agent=researcher
    )
    
    print(f"\n[+] CrewAI Agent configured (using {OPENAI_MODEL})")
    print(f"    Role: {researcher.role}")
    print(f"    Goal: {researcher.goal}")
    
    # 3. Governance check
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
    
    print("\nDemo complete.")

if __name__ == "__main__":
    run_governed_crew()
