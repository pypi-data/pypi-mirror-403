# Refactoring & Reframing Guide

To harden the Agent Harness into a pure engineering system, EmoCore concepts must be reframed from "emotion-inspired" to "deterministic control-state".

**Goal:** Shift from "affective regulation" to "deterministic control-state evaluation under bounded execution".

## 1. Vocabulary Changes

**Rule:** If a kernel engineer would roll their eyes, rename it.

| Old Term (Kill) | New Term (Engineering) |
| :--- | :--- |
| **Emotion** | **Control State** |
| **Appraisal** | **State Evaluation** |
| **Affective Signal** | **Control Signal** |
| **Frustration** | **Controllability Loss** |
| **Pressure** | **Accumulated Load** |
| **Mood** | **Execution Mode** |

## 2. Reframe "Appraisal"

**Rename:** `Appraisal` → `StateEvaluator`

**What it is:**
*   A deterministic function
*   Operating over bounded state
*   Producing no side effects
*   With explicit priority ordering

**New Definition:**
> **State Evaluation** is the deterministic classification of execution viability given accumulated load, remaining budgets, and recent system dynamics.

## 3. Reframe the Signal Model

Signals are engineering-grade, not psychological.

| Signal | Reframe As |
| :--- | :--- |
| **Reward** | **Progress Gradient** |
| **Novelty** | **State Space Expansion** |
| **Urgency** | **Constraint Tightening** |
| **Difficulty** | **Control Loss Index** |

**Example rewrite:**
> "Difficulty represents loss of controllability under repeated execution attempts, not subjective failure."

## 4. Renaming EmoCore

EmoCore is the **engine**, not the brand.

**Recommendation:** `GovernanceKernel`

*   **Kernel** = small, trusted, boring, immutable
*   **Governance** = permission, not intelligence

**New Identity:**
> A deterministic governance kernel that evaluates execution viability under bounded budgets and accumulated load, independent of agent intelligence or intent.

## 5. What to Keep Exactly As-Is (Load-Bearing)

Do not change these guarantees:
*   Pessimistic-by-default stance
*   Deterministic halting
*   Budget monotonicity
*   Typed failure modes
*   External reset requirement
*   "Bad observability → less agency" rule
