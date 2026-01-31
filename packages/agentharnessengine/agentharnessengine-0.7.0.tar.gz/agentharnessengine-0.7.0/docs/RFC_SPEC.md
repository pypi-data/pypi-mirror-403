RFC-AH-0001

Agent Harness: Deterministic Runtime Governance for Autonomous Agents

Status: Draft
Category: Standards Track
Author: —
Last Updated: 2026-01-28


---

Abstract

This document specifies the Agent Harness, a runtime control system for autonomous agents.
An Agent Harness enforces bounded, deterministic, fail-closed execution of agents by governing their actions externally at runtime, independent of internal reasoning, model behavior, or intent.

This specification defines:

Required guarantees

Formal components

Execution semantics

Failure taxonomy

Audit and determinism requirements

Conformance criteria



---

1. Introduction

Autonomous agents differ fundamentally from traditional AI systems in that they act: invoking tools, modifying state, and interacting with environments over time. Existing governance approaches focused on design-time policies or model outputs are insufficient to control such systems during execution.

The Agent Harness addresses this gap by introducing a runtime execution control boundary that enforces hard constraints on agent behavior.


---

2. Terminology

The key words MUST, MUST NOT, SHALL, SHOULD, MAY, and REQUIRED are to be interpreted as described in RFC 2119.

Agent: A system capable of autonomous decision-making and action execution.

Harness: An external runtime control system governing an agent.

Action: Any operation that produces side effects outside the agent’s internal state.

Signal: An observed fact about execution.

Budget: A bounded allowance governing execution.

Evaluator: A deterministic function deciding continuation or halt.

Enforcer: A mechanism that physically allows or blocks actions.

Halt: Final termination of execution by the harness.



---

3. Non-Goals

An Agent Harness MUST NOT:

Modify agent reasoning or planning

Improve task performance or correctness

Learn or adapt governance policies

Predict agent success or failure

Interpret intent or semantics


The harness governs execution, not intelligence.


---

4. Core Guarantees

A conformant Agent Harness MUST guarantee all of the following:

1. Finite Execution
An agent MUST NOT be able to execute indefinitely.


2. Fail-Closed Enforcement
Once halted, no further actions MAY be executed without explicit external reset.


3. Deterministic Governance
Given identical inputs (signals, budgets, configuration), the harness MUST produce identical decisions.


4. Typed Halting
Every halt MUST have an explicit, categorical reason.


5. External Control
The agent MUST NOT be able to bypass, disable, or override governance.



Failure to meet any guarantee disqualifies an implementation as an Agent Harness.


---

5. Architectural Placement

The harness MUST exist outside the agent’s reasoning loop.

Valid placements include:

Execution loop controller

Tool invocation gate

System or network boundary (proxy / sidecar)


A harness implemented solely within agent code is NON-CONFORMANT.


---

6. Conceptual Model

An Agent Harness is composed of four orthogonal subsystems:

Signals → Budgets → Evaluator → Enforcer

Each subsystem MUST be independently testable.


---

7. Signals

7.1 Definition

Signals are observations of execution.
They MUST describe what happened, not what should happen.

7.2 Required Signal Classes

A conformant harness MUST support at least:

Effort Signals

steps

time

compute


Progress Signals

completion delta

novelty

repeated states


Failure Signals

retries

errors

exceptions


Risk Signals

action category

permission escalation

external side effects



Signals MUST be:

monotonic where applicable

additive

side-effect free



---

8. Budgets

8.1 Definition

Budgets define allowed execution capacity.

8.2 Properties

Budgets MUST be:

finite

bounded

monotonically non-increasing

non-replenishing (without external reset)


8.3 Canonical Budget Dimensions

A conformant harness MUST support:

Effort Budget

Persistence Budget

Risk Budget

Exploration Budget



---

9. Evaluator

9.1 Definition

The evaluator is a pure deterministic function:

Decision = f(Signals, Budgets, State)

9.2 Properties

The evaluator MUST:

be deterministic

have no side effects

be reproducible

be explainable via inputs


9.3 Outputs

The evaluator MUST output exactly one of:

ALLOW

HALT(reason)



---

10. Failure Taxonomy

A harness MUST classify halts into explicit categories.

Required Halt Reasons

EXHAUSTION – effort budget depleted

STAGNATION – no progress across window

PERSISTENCE_LIMIT – retry tolerance exceeded

OVERRISK – risk threshold crossed

EXPLORATION_DRIFT – novelty exceeds bounds

EXTERNAL – externally imposed stop


Halt reasons MUST be final and immutable.


---

11. Enforcement Layer

11.1 Definition

The enforcement layer physically enacts governance decisions.

11.2 Requirements

The enforcement layer MUST:

intercept all actions

block actions on HALT

be synchronous with action attempts

be outside agent control


An enforcement layer that can be bypassed by the agent is NON-CONFORMANT.


---

12. Audit & Trace

12.1 Requirements

A harness MUST emit an execution trace that is:

append-only

ordered

immutable

machine-readable


12.2 Required Trace Fields

Each trace entry MUST include:

step index

observed signals

remaining budgets

evaluator decision

halt reason (if applicable)


The trace MUST be sufficient to reconstruct governance decisions.


---

13. Determinism Boundary

Component	Determinism

Agent reasoning	Non-deterministic
Environment	Partially deterministic
Evaluator	Fully deterministic
Enforcement	Fully deterministic


Governance correctness MUST NOT depend on model behavior.


---

14. Multi-Agent Generalization

An Agent Harness MAY govern systems of agents via:

shared budgets

aggregate risk

cross-agent stagnation detection

cascading halts


System-level governance MUST preserve all single-agent guarantees.


---

15. Security Model

The harness MUST assume:

the agent may be faulty

the agent may be adversarial

the agent may be compromised


Governance MUST therefore be:

fail-closed

external

non-bypassable



---

16. Conformance Criteria

An implementation is a conformant Agent Harness if and only if:

1. Agents cannot exceed execution limits


2. Halting is deterministic and typed


3. All actions pass through enforcement


4. Governance state is auditable


5. Execution is provably finite



Failure of any criterion results in non-conformance.


---

17. Relationship to EmoCore

EmoCore supplies:

budget abstractions

deterministic halt logic

failure taxonomy


An Agent Harness:

incorporates EmoCore as its governance engine

adds enforcement, auditability, and execution boundaries


EmoCore alone is necessary but not sufficient.


---

18. One-Sentence Definition

> An Agent Harness guarantees that autonomous agents cannot cause unbounded behavior, regardless of intelligence, intent, or failure mode.




---

End of RFC-AH-0001
