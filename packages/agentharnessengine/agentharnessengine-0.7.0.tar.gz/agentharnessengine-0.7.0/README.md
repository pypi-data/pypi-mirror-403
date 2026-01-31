# Governance

![PyPI version](https://img.shields.io/pypi/v/agentharnessengine)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

**Governance** is a rigorous engineering kernel for AI agents. It enforces the "World & IBM" 15-point checklist for safe, deterministic, and bounded autonomous systems. 

It sits between your agent's brain and its hands, translating abstract signals (reward, novelty, urgency) into hard execution boundaries.

---

## The 15-Point Governance Checklist

This package solves the "Unbounded Behavior" problem by default.

### 1. Unbounded Behavior
> “We cannot allow systems that run indefinitely.”
- **Solution**: `governance` strictly ties execution to a finite budget (`effort`, `persistence`). When budget reaches zero, the agent **HALTS**. No infinite loops, no endless retries.

### 2. Runtime Control
> “Policies written before deployment don’t matter at runtime.”
- **Solution**: Dynamic `step()` evaluation updates control state *during* execution. If `risk` spikes or `progress` stalls, the kernel intervenes immediately, overriding the agent's intent.

### 3. Deterministic Behavior
> “We need predictable outcomes, not vibes.”
- **Solution**: The kernel is a deterministic state machine. Same signal sequence $\rightarrow$ Same internal state $\rightarrow$ Same halt decision. Zero stochasticity in enforcement.

### 4. Explainable Halting
> “If it stops, we must know why.”
- **Solution**: Every halt returns a precise `FailureType` (`EXHAUSTION`, `STAGNATION`, `OVERRISK`, `SAFETY`) and a human-readable reason string.

### 5. Fail-Closed Semantics
> “When something goes wrong, stop — don’t guess.”
- **Solution**: If telemetry is missing or trust is low, the kernel defaults to safety. Once halted, the system remains halted (terminal state) until explicit manual reset.

### 6. Physical Enforcement
> “Advisory systems are not governance.”
- **Solution**: The `InProcessEnforcer` (and future proxy/sidecar patterns) physically blocks tool execution when the kernel halts. It raises `EnforcementBlocked`, preventing the action from occurring.

### 7. Auditability & Traceability
> “Show us exactly what happened.”
- **Solution**: `AuditLogger` records an immutable, append-only ledger of every step, signal, budget state, and decision.

### 8. Accountability Attribution
> “Who authorized this action?”
- **Solution**: Every decision is cryptographically linked to a specific step and agent identity in the audit log.

### 9. Risk Containment
> “The system must not escalate itself.”
- **Solution**: Explicit `risk` budget. As urgency scales, risk tolerance may increase slightly, but hard caps (`max_risk`) prevent catastrophic escalation.

### 10. Progress vs Activity Discrimination
> “Busy ≠ productive.”
- **Solution**: The `stagnation_window` detects "spinning" (actions with low reward). It depletes `effort` rapidly when an agent is active but ineffective.

### 11. Resilience to Bad Telemetry
> “If sensors lie, slow down.”
- **Solution**: The `trust` signal dampens positive inputs (reward/novelty) validation but passes negative inputs (difficulty/urgency) fully. Noisy data leads to conservative behavior.

### 12. Model-Agnosticism
> “We will swap models constantly.”
- **Solution**: Works with **LangChain**, **AutoGen**, **CrewAI**, or raw loops. It checks *signals*, not prompts or model weights.

### 13. Human Override & Recovery
> “Humans must remain the final authority.”
- **Solution**: `reset()` is a privileged operation. The system cannot restart itself; a human (or supervisor process) must authorize a new budget.

### 14. Compliance Readiness
> “We don’t want to rebuild this for every law.”
- **Solution**: Generates standardized JSON artifacts (`trace.json`) suitable for regulatory introspection.

### 15. Scalability Across Agent Systems
> “This won’t be one agent.”
- **Solution**: `SystemGovernor` manages shared budget pools across swarms, detecting cascades and ensuring no single agent hogs resources.

---

## Installation

```bash
pip install agentharnessengine
```

*(Note: Requires Python 3.10+)*

---

## Quick Start

```python
from governance import GovernanceKernel, step, Signals

# 1. Initialize the Kernel
kernel = GovernanceKernel()

# 2. Run your agent loop
while True:
    # ... Agent thinks and chooses an action ...
    
    # 3. Feed signals to Governance
    #    reward: 0.0-1.0 (Did we make progress?)
    #    novelty: 0.0-1.0 (Is this new info?)
    #    urgency: 0.0-1.0 (Are we out of time?)
    result = step(kernel, Signals(reward=0.5, novelty=0.1, urgency=0.0))
    
    # 4. ENFORCE
    if result.halted:
        print(f"🛑 HALTED: {result.failure} - {result.reason}")
        break
        
    # 5. Execute action only if allowed
    print(f"✅ GO: Effort={result.budget.effort:.2f}")
```

## How It Works

**Pressure** (unbounded, accumulates) $\rightarrow$ **Budget** (bounded [0,1], generally decreases).

- **Effort**: Fuel. Burns with time and activity.
- **Risk**: Thermometer. Freezes actions when too hot.
- **Persistence**: Grip strength. How long to try before giving up.
- **Exploration**: Leash length. How far to stray for new info.

Unlike RL or policies, **Governance** is not trying to maximize reward. It is trying to **guarantee limits**.

## Architecture

```text
Environment (Signals)
      │
      ▼
[Governance Kernel] ──▶ Audit Log
      │
      ▼
 Decision (Halt/Go)
      │
      ▼
  Enforcement
```

## License

MIT
