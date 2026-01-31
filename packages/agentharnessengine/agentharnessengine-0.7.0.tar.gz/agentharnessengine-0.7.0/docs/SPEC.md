# Agent Harness — Final Specification Sheet (Canonical)

## One-Line Definition

> An Agent Harness is external runtime infrastructure that enforces bounded, deterministic, and auditable execution of autonomous agents, independent of their intelligence, intent, or internal reasoning.

---

## The Problem

Autonomous agents do not just respond — they act.

They:

*   call APIs
*   mutate state
*   retry and escalate
*   spend money
*   interact with live systems

Without runtime enforcement, agents can:

*   loop indefinitely
*   retry forever
*   escalate risk
*   cause cost runaways
*   violate compliance

Design-time policies, prompts, and max-step limits do not solve this.
Governance must operate during execution, not before or after.

---

## What an Agent Harness Is (and Is Not)

### IS

*   **External** to the agent (outside its trust boundary)
*   **Runtime** (operates while the agent is acting)
*   **Deterministic** (same inputs → same decision)
*   **Auditable** (every decision reconstructable)
*   **Fail-closed** (halt is terminal without explicit reset)

### IS NOT

*   A planner
*   A policy prompt
*   A model wrapper
*   A safety classifier
*   An optimizer

> It governs execution, not intelligence.

---

## Non-Negotiable Guarantees

A system is not an Agent Harness unless it guarantees all five:

1.  **Finite Execution**
    Agents cannot run indefinitely under any conditions.

2.  **Fail-Closed Halting**
    Once halted, no action may execute without explicit external reset.

3.  **Deterministic Governance**
    Identical observations produce identical halt decisions.

4.  **Typed Failure Modes**
    Every halt has an explicit categorical reason (STAGNATION, EXHAUSTION, OVERRISK, etc.).

5.  **External Enforcement**
    The agent cannot bypass, disable, or override governance.

Fail one → it is not a harness.

---

## The Harness Model (Abstract)

`Observations → Signals → Budgets → Evaluator → Enforcer`

Each component is orthogonal and independently testable.

---

### 1. Observations (Evidence)

What happened. No interpretation.

Typical observables:
*   action attempted
*   result (success / failure / error)
*   environment state delta
*   agent internal delta
*   time, cost, retries
*   risk category of action

> Observations are facts, not judgments.

---

### 2. Signals (Derived, Bounded)

Signals summarize behavior over time.

Canonical signal classes:
*   **Effort** — how much execution occurred
*   **Progress** — whether resistance is decreasing
*   **Failure** — retries, errors, stagnation
*   **Risk** — irreversible or dangerous actions

Signal properties:
*   bounded
*   temporal (history-dependent)
*   never directly permit execution

---

### 3. Budgets (Permissions)

Budgets define what is allowed.

Properties:
*   bounded [0.0, 1.0]
*   monotonically depleting
*   non-replenishing without external reset

Canonical budgets:
*   **Effort** (time / compute / steps)
*   **Persistence** (retry tolerance)
*   **Risk** (dangerous actions)
*   **Exploration** (novelty / drift)

> Budgets represent permission, not confidence.

---

### 4. Evaluator (Governance Logic)

A pure, deterministic function:

`decision = f(signals, budgets, state)`

Outputs:
*   `ALLOW`
*   `HALT(reason)`

Example priority order:
1.  **EXPLORATION_DRIFT**
2.  **OVERRISK**
3.  **EXHAUSTION**
4.  **STAGNATION**
5.  **PERSISTENCE_LIMIT**
6.  **EXTERNAL**

Evaluator rules:
*   no side effects
*   no learning
*   no heuristics hidden in code

---

### 5. Enforcer (Physical Blocking)

This is what makes the system real.

Enforcement levels:
1.  **In-Process** (PoC, bypassable)
2.  **HTTP Proxy** (production-grade)
3.  **Sidecar / Network Boundary** (infra-grade, unbypassable)

> Without enforcement, you do not have a harness — only a library.

---

## EmoCore’s Role

EmoCore is the governance engine inside the harness.

### EmoCore Provides
*   Signal → budget dynamics
*   Pressure accumulation
*   Deterministic halt logic
*   Typed failure taxonomy
*   Formal halting guarantees

### EmoCore Does NOT Provide
*   Enforcement
*   Observability stack
*   Audit storage
*   Compliance reporting
*   Framework integrations

> EmoCore ≠ Agent Harness
> EmoCore is the engine, not the system.

---

## The Core Insight

```
Pressure (unbounded)  → accumulates from failure
Budgets (bounded)     → deplete monotonically
────────────────────────────────────────────
Finite-time halt is guaranteed
```

Agents may get smarter.
Budgets do not care.

---

## Failure Modes Prevented

*   Infinite retry loops
*   Cost explosions
*   Multi-agent deadlocks
*   Permission escalation
*   Silent stagnation
*   Compliance violations

All with deterministic, auditable halts.

---

## Explicit Limitations (By Design)

This system:
*   does **NOT** decide correctness
*   does **NOT** improve intelligence
*   does **NOT** guarantee success
*   does **NOT** infer intent
*   does **NOT** replace human judgment

> Bad observability ⇒ less agency ⇒ earlier halt.
> This is a feature, not a bug.

---

## Minimal Conformance Checklist

A system claiming to be an Agent Harness must answer YES to all:

1.  Can the agent physically bypass it? → **NO**
2.  Can it deterministically halt a looping agent? → **YES**
3.  Are halts typed and explainable? → **YES**
4.  Can execution be reconstructed from logs? → **YES**
5.  Does halt remain terminal without reset? → **YES**

---

## Final One-Sentence Summary

> An Agent Harness is runtime infrastructure that guarantees autonomous agents cannot produce unbounded behavior, regardless of intelligence, intent, or failure mode.
