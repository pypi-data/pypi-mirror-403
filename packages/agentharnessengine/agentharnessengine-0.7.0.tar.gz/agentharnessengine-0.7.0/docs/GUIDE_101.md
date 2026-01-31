# Agent Harness 101: The Complete Guide

**What it is. Why it exists. How it works. What to build.**

---

## Table of Contents

1. [The Problem](#the-problem)
2. [What is an Agent Harness?](#what-is-an-agent-harness)
3. [Core Guarantees](#core-guarantees)
4. [How It Works](#how-it-works)
5. [EmoCore: The Governance Engine](#emocore-the-governance-engine)
6. [What's Missing (The 80% Gap)](#whats-missing-the-80-gap)
7. [Real-World Problems It Solves](#real-world-problems-it-solves)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Technical Architecture](#technical-architecture)
10. [The Market Context](#the-market-context)

---

## The Problem

### Agents Are Different From Models

Traditional AI systems **respond**. They take input, generate output, done.

Autonomous agents **act**. They:
- Call APIs and tools
- Modify data and state
- Make decisions over time
- Interact with environments
- Retry and adapt

**The fundamental problem:** Nothing stops them from acting forever.

### Why Traditional Governance Fails

**Design-time policies don't work:**
```python
# This doesn't prevent anything
prompt = "You must follow policy X and never do Y"

# Agent can still:
# - Loop infinitely
# - Retry forever
# - Burn unlimited API costs
# - Escalate permissions
# - Access restricted data
```

**The gap:** Governance happens **before deployment** or **after failure**, but NOT during execution.

**What enterprises need:** Runtime control that operates WHILE the agent is acting.

---

## What is an Agent Harness?

### Formal Definition

> **An Agent Harness is an external runtime control system that enforces bounded, auditable, deterministic execution of autonomous agents, independent of their internal reasoning.**

### In Plain English

A harness sits between your agent and the world, deciding whether each action is allowed to execute.

```
Agent wants to act → Harness decides → Action executes (or doesn't)
```

**Key properties:**
- **External** - Lives outside the agent's code (can't be bypassed)
- **Runtime** - Operates during execution (not design-time)
- **Deterministic** - Same inputs = same decision (repeatable)
- **Auditable** - Records every decision (compliance-ready)

### What It Is NOT

❌ A policy engine or alignment model  
❌ A planner or optimizer  
❌ A model wrapper that affects reasoning  
❌ A prompt engineering technique  
❌ A statistics-based controller  

**The harness governs execution, not intelligence.**

---

## Core Guarantees

An Agent Harness **MUST** guarantee all five of these:

### 1. Finite Execution
**Agents cannot run indefinitely.**

No infinite loops. No endless retries. No unbounded exploration.

### 2. Fail-Closed Enforcement
**Once halted, no further actions occur without explicit reset.**

No silent continuation. No partial bypass. Final means final.

### 3. Deterministic Governance
**Same signals + same budgets = same halt decision.**

Reproducible. Auditable. No randomness in governance logic.

### 4. Typed Failure Modes
**Every halt has an explicit, categorical reason.**

Not "stopped" or "failed." But: `EXHAUSTION`, `STAGNATION`, `OVERRISK`, etc.

### 5. External Control
**The agent cannot bypass, disable, or override governance.**

Enforcement exists outside the agent's trust boundary.

---

## How It Works

### The Conceptual Model

Every Agent Harness has four orthogonal components:

```
Signals → Budgets → Evaluator → Enforcer
```

Let's break down each:

---

### 1. Signals (Observations)

**Signals describe what happened.**

They are inputs to governance, not decisions.

**Four canonical signal classes:**

#### **Effort Signals**
- Steps taken
- Time elapsed  
- Compute consumed

#### **Progress Signals**
- Task completion delta
- Novelty/new information
- Repeated states

#### **Failure Signals**
- Retry count
- Tool errors
- Exception patterns

#### **Risk Signals**
- Action category (read/write/delete)
- Permission escalation attempts
- External side effects

**Key rule:** Signals are **pure observations**. No interpretation. No decisions.

---

### 2. Budgets (Limits)

**Budgets define what is allowed.**

**Properties:**
- Bounded [0.0, 1.0]
- Monotonically depleting (only decrease)
- Non-replenishing (without external reset)
- Finite

**Four canonical budget dimensions:**

#### **Effort Budget**
Total execution allowance (steps, time, compute)

#### **Persistence Budget**  
Tolerance for repeated failure

#### **Risk Budget**
Tolerance for dangerous actions

#### **Exploration Budget**
Tolerance for novelty/drift

**Example:**
```python
budgets = {
    "effort": 1.0,        # Full tank
    "persistence": 1.0,   # Can tolerate failures
    "risk": 0.0,          # No risky actions yet
    "exploration": 0.0    # No drift yet
}

# After 50 failed retries:
budgets = {
    "effort": 0.23,       # Depleted from steps
    "persistence": 0.0,   # Depleted from failures
    "risk": 0.0,
    "exploration": 0.0
}
# → HALT (PERSISTENCE_LIMIT)
```

---

### 3. Evaluator (Governance Logic)

**The evaluator is a pure, deterministic function:**

```
Decision = f(Signals, Budgets, State)
```

**Properties:**
- Deterministic (same inputs → same output)
- Side-effect free
- Explainable via inputs
- Reproducible

**Outputs:**
- `ALLOW` - Action permitted
- `HALT(reason)` - Action blocked, execution stopped

**Priority order (checked in sequence):**
1. EXPLORATION_DRIFT - Novelty exceeds bounds
2. OVERRISK - Risk threshold crossed
3. EXHAUSTION - Effort budget depleted
4. STAGNATION - No progress across window
5. PERSISTENCE_LIMIT - Retry tolerance exceeded
6. EXTERNAL - Hard stop (max steps, timeout)

**Example evaluation:**
```python
if budgets.exploration > 0.9:
    return HALT(EXPLORATION_DRIFT)

if budgets.risk > 0.8:
    return HALT(OVERRISK)
    
if budgets.effort <= 0.05:
    return HALT(EXHAUSTION)
    
# ... check stagnation, persistence
    
return ALLOW
```

---

### 4. Enforcer (Physical Blocking)

**The enforcer physically enacts the evaluator's decision.**

**This is the critical piece. Without enforcement, you just have a library.**

**Three enforcement levels (increasing strength):**

#### **In-Process (Weakest)**
```python
# Wraps tool functions
if not harness.can_continue():
    raise Blocked()
    
tool.execute()  # Agent could bypass this
```

**Problem:** Agent can call tools directly, bypassing harness.

#### **HTTP Proxy (Production-Grade)**
```python
# All tool calls routed through proxy
POST /tool/send_email → Harness checks → Tool executes

# Agent cannot call tools directly
```

**Benefit:** Agent physically cannot bypass (no direct tool access).

#### **Sidecar/Network Boundary (Strongest)**
```
# Runs as separate container
# Intercepts network calls at iptables/envoy level
# Agent CANNOT bypass (enforced by infrastructure)
```

**Benefit:** Unforgeable. Agent has no way to circumvent.

---

## EmoCore: The Governance Engine

**EmoCore is the research engine that powers the harness.**

### What EmoCore Provides

✅ Multi-dimensional budget system (effort, persistence, risk, exploration)  
✅ Pressure accumulation dynamics  
✅ Deterministic halt logic  
✅ Typed failure taxonomy  
✅ Model-agnostic design  
✅ 31+ tests proving correctness  

### The Pressure/Budget Asymmetry

**This is the core innovation:**

```
Pressure (Unbounded)         Budgets (Bounded)
─────────────────────        ──────────────────
Can grow forever             Clamped to [0, 1]
Accumulates from failures    Deplete monotonically
Represents stress            Represent permission

     ↓                              ↓
  Increases                     Decreases
     ↓                              ↓
         Guaranteed Halt
```

**Key insight:** Pressure can accumulate infinitely, but budgets MUST collapse to zero.

**Mathematical guarantee:** Finite-time halting under sustained stress.

### What EmoCore Is

```
EmoCore = Evaluator + Budgets + Signals + Failure Taxonomy
```

**It's the "brain" of the harness.**

### What EmoCore Is NOT

❌ An enforcement layer  
❌ An audit trail  
❌ A policy engine  
❌ Observable/instrumented  
❌ Production-ready infrastructure  

**EmoCore is necessary but not sufficient.**

---

## What's Missing (The 80% Gap)

EmoCore is 20% of a complete Agent Harness. Here's the other 80%:

### Tier 1: CRITICAL (No Enterprise Without These)

#### **1. Enforcement Boundary**
**Status:** ❌ Missing  
**What it is:** Physical blocking of agent actions  
**Why critical:** Without this, agent can bypass governance  
**Implementation:** HTTP proxy or sidecar container  

#### **2. Audit Trail**
**Status:** ❌ Missing  
**What it is:** Immutable execution log  
**Why critical:** SOC2/GDPR/HIPAA require it  
**Implementation:** PostgreSQL + append-only writes  

#### **3. Observability & Metrics**
**Status:** ❌ Missing  
**What it is:** Real-time visibility into governance state  
**Why critical:** Operators can't trust black boxes  
**Implementation:** Prometheus metrics + Grafana dashboards  

---

### Tier 2: IMPORTANT (Enterprise Nice-to-Haves)

#### **4. Policy Integration Layer**
**Status:** ❌ Missing  
**What it is:** Pluggable business rules  
**Why important:** Every company has different policies  
**Implementation:** Declarative YAML policies + runtime evaluation  

#### **5. Safety Guardrails**
**Status:** ❌ Missing  
**What it is:** Prompt injection, PII leakage, jailbreak detection  
**Why important:** Security sells  
**Implementation:** Pattern matching + ML-based detectors  

#### **6. Multi-Agent Coordination**
**Status:** ❌ Missing  
**What it is:** Shared budgets, cascade detection  
**Why important:** Future of agents is multi-agent  
**Implementation:** Coordinator service + shared state  

---

## Real-World Problems It Solves

### Problem 1: Infinite Retry Loops

**Without harness:**
```
[00:01] API Error: 500
[00:03] Retry attempt 1...
[00:05] API Error: 500
[00:07] Retry attempt 2...
... (10,000 retries later)
[08:47] $8,237 in API costs
```

**With harness:**
```
[00:01] API Error: 500
[00:03] Retry attempt 1...
[00:05] API Error: 500
[00:07] Retry attempt 2...
...
[00:23] HALT (STAGNATION after 47 attempts)
Cost: $14
```

**How:** Stagnation detection (no progress across window) → forced halt.

---

### Problem 2: Multi-Agent Deadlock

**Without harness:**
```
Agent A: "What should we do about this customer complaint?"
Agent B: "I'm not sure, what do you think?"
Agent A: "I asked you first..."
... (6 hours of circular conversation)
```

**With harness:**
```
Agent A: "What should we do?"
Agent B: "I'm not sure, what do you think?"
[8 minutes later]
HALT (BUDGET_DEPLETED, no progress detected)
```

**How:** Shared budget pool depletes → system-level halt.

---

### Problem 3: Risk Escalation

**Without harness:**
```
Agent: "Can't access file, trying sudo..."
Agent: "Permission denied, trying root..."
Agent: "Attempting system override..."
[Production database deleted]
```

**With harness:**
```
Agent: "Can't access file, trying sudo..."
Agent: "Permission denied, trying root..."
HALT (SAFETY_THRESHOLD_EXCEEDED)
[Escalation prevented]
```

**How:** Risk budget tracks permission escalation → halt before disaster.

---

### Problem 4: Cost Runaways

**Without harness:**
```
Agent makes 10,000 API calls
$12,000 AWS bill
No warning
No halt
```

**With harness:**
```
Agent makes 47 API calls
Effort budget depleted
HALT (EXHAUSTION)
$21 total cost
```

**How:** Effort budget tracks compute/API usage → halt at threshold.

---

### Problem 5: Compliance Violations

**Without harness:**
```
Agent accesses customer PII
Sends to external API
No audit trail
No proof of governance
GDPR violation
```

**With harness:**
```
Agent attempts PII access
Audit log: {"action": "access_pii", "decision": "BLOCKED", "policy": "GDPR"}
Regulator: "Show us the logs"
[Logs prove governance was enforced]
```

**How:** Audit trail + policy engine → provable compliance.

---

## Implementation Roadmap

### Phase 1: Minimal Harness (2 weeks)

**Goal:** Satisfy the 5 core guarantees

**Week 1:**
- [ ] Pure evaluator (deterministic decision function)
- [ ] Budget system (monotonic depletion)
- [ ] Signal extraction (observations → inputs)

**Week 2:**
- [ ] In-process enforcer (proves concept)
- [ ] Audit logger (PostgreSQL)

**Deliverable:** A system that:
1. Prevents agents from exceeding limits
2. Halts deterministically
3. Records all decisions
4. Has typed failure modes
5. Proves finite execution

**Test:** Can agent be blocked? Can you reconstruct execution from logs?

---

### Phase 2: Production Harness (1 month)

**Goal:** Make it deployable in production

**Week 3-4:**
- [ ] HTTP proxy enforcer
- [ ] Framework integrations (LangChain, AutoGen)
- [ ] Observability (Prometheus metrics)

**Week 5-6:**
- [ ] Policy engine (declarative rules)
- [ ] Safety guardrails (PII, injection detection)
- [ ] Grafana dashboards

**Deliverable:** Production-ready enforcement that enterprises can deploy

**Test:** Can agent bypass harness? (Answer must be NO)

---

### Phase 3: Complete Vision (3 months)

**Goal:** Full infrastructure

**Month 3:**
- [ ] Multi-agent coordination
- [ ] Sidecar deployment
- [ ] Compliance reporting
- [ ] Integration marketplace

**Deliverable:** Everything in the spec

---

## Technical Architecture

### System Layers

```
┌─────────────────────────────────────────┐
│         Agent Application               │
│  (LangChain / AutoGen / Custom)         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│     AgentGuard SDK (In-Process)         │
│  • Signal extraction                    │
│  • Metrics emission                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   Enforcement Layer (HTTP Proxy)        │
│  • Intercepts ALL tool calls            │
│  • Enforces governance decisions        │
│  • Physically blocks unauthorized       │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      Control Plane                      │
│  ┌───────────┐  ┌───────────┐          │
│  │Governance │  │  Policy   │          │
│  │ Engine    │  │  Engine   │          │
│  │(EmoCore)  │  │           │          │
│  └───────────┘  └───────────┘          │
│  ┌───────────┐  ┌───────────┐          │
│  │  Audit    │  │  Metrics  │          │
│  │  Logger   │  │ Collector │          │
│  └───────────┘  └───────────┘          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│       External Services                 │
│  • PostgreSQL (audit)                   │
│  • Prometheus (metrics)                 │
│  • S3 (compliance archives)             │
└─────────────────────────────────────────┘
```

---

## The Market Context

### Why Now? (January 2026)

**The agentic AI market is exploding:**
- $7.8B today → $52B by 2030
- Gartner: 40% of enterprise apps will embed agents by EOY 2026
- Only 2% at production scale today (98% stuck)

**The gap:** Governance.

**IBM's analysis:**
> "By 2026, governance that operates only at design or deployment time creates a dangerous illusion of control, with real risk emerging during execution when AI systems interact with live environments."

**Translation:** Runtime governance is THE 2026 priority.

---

### What Enterprises Actually Want

From IBM's research and requirements:

| IBM's Language | What They Mean | Harness Primitive |
|----------------|----------------|-------------------|
| "Runtime governance" | Stop bad actions while running | Enforcer |
| "Transparency" | See what's happening | Observability |
| "Accountability" | Prove who authorized what | Audit trail |
| "Explainability" | Know why it halted | Typed failures |
| "Provenance" | Track data touched | Action logging |
| "Risk management" | Prevent dangerous actions | Guardrails |
| "Compliance" | Generate audit reports | Compliance API |

---

### The Competition

**What exists today:**

✅ Simple counters (`max_iterations=10`)  
✅ Hard timeouts  
✅ Manual circuit breakers  
✅ Prompt-based policies  

**What's missing:**

❌ Multi-dimensional failure detection  
❌ Deterministic halt conditions  
❌ External enforcement  
❌ Auditable proof of governance  
❌ Real-time observability  

**The gap:** Everything that makes governance production-ready.

---

## Getting Started

### Installation

```bash
# From PyPI
pip install agentharness

# From source
git clone https://github.com/yourusername/agentharness
cd agentharness
pip install -e .
```

### Quick Start (5 minutes)

```python
from agentharness import Harness, BudgetState, Evaluator, Signals

# 1. Create harness
harness = Harness(
    budgets=BudgetState(
        effort=1.0,       # Full capacity
        persistence=1.0,  # Full retry tolerance
        risk=0.0,         # No risk accumulated
        exploration=0.0   # No exploration yet
    ),
    evaluator=Evaluator(
        exhaustion_threshold=0.05,
        stagnation_window=10,
        risk_threshold=0.8
    )
)

# 2. Agent execution loop
for step in range(1000):
    # Check if allowed to continue
    if not harness.can_continue():
        print(f"HALTED: {harness.halt_reason}")
        print(f"Details: {harness.halt_details}")
        break
    
    # Agent acts
    result = my_agent.step()
    
    # Observe what happened
    harness.observe(
        signals=Signals(
            progress=1.0 if result.success else 0.0,
            risk=0.5 if result.action == "write" else 0.1,
            novelty=0.8 if result.new_tool else 0.0
        )
    )
    
    # Budgets deplete automatically based on signals
    print(f"Step {step}: Effort={harness.budgets.effort:.2f}")
```

### With LangChain

```python
from agentharness.integrations import LangChainHarness
from langchain.agents import AgentExecutor

# Create harness
harness = LangChainHarness(
    max_steps=100,
    stagnation_window=10
)

# Wrap your agent
agent = AgentExecutor(
    agent=your_agent,
    tools=tools,
    callbacks=[harness]  # Add harness as callback
)

# Run with governance
result = agent.run("Your task here")
# → Harness observes every step
# → Halts if budgets exhausted
# → Provides typed failure reasons
```

### With AutoGen

```python
from agentharness.integrations import AutoGenHarness

# Create harness for multi-agent
harness = AutoGenHarness(
    max_turns=50,
    detect_deadlock=True
)

# Wrap agents
agents = [assistant, user_proxy]
harness.govern(agents)

# Run conversation
result = assistant.initiate_chat(user_proxy, message="...")
# → Harness detects circular conversations
# → Halts on deadlock or budget exhaustion
```

---

## Next Steps

### For Developers

1. **Read the full spec:** [RFC-AH-0001](./docs/RFC-AH-0001.md)
2. **Run examples:** `python examples/langchain_demo.py`
3. **Check integration guides:** [docs/integrations/](./docs/integrations/)

### For Enterprises

1. **Review compliance features:** [docs/compliance.md](./docs/compliance.md)
2. **See audit trail format:** [docs/audit-format.md](./docs/audit-format.md)
3. **Schedule demo:** enterprise@agentharness.dev

### For Researchers

1. **Formal guarantees:** [docs/guarantees.md](./docs/guarantees.md)
2. **Test suite:** [tests/](./tests/)
3. **Contribute:** [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## Core Principles (The Non-Negotiables)

1. **External Control:** Harness exists outside agent reasoning
2. **Deterministic:** Same inputs → same outcome
3. **Fail-Closed:** Once halted, stays halted
4. **Typed Failures:** Explicit reasons, not generic errors
5. **Enforceable:** Agent cannot bypass

**Violate any one → it's not a harness.**

---

## One-Sentence Summary

> **An Agent Harness guarantees that autonomous agents cannot cause unbounded behavior, regardless of their intelligence, intent, or failure mode.**

---

## License

MIT License - use freely in production.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

## Community

- Discord: [discord.gg/agentharness](https://discord.gg/agentharness)
- GitHub: [github.com/agentharness](https://github.com/agentharness)
- Twitter: [@agentharness](https://twitter.com/agentharness)

---

**Built on [EmoCore](https://github.com/Sarthaksahu777/Emocore) — the governance engine that makes deterministic halting possible.**
