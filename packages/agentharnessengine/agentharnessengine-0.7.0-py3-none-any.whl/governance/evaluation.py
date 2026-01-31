# emocore/evaluation.py
"""
SignalEvaluator: Converts environmental signals into control state deltas.

What SignalEvaluator does:
- Takes reward, novelty, urgency signals from the environment
- Produces state DELTAS for all canonical control axes
- These deltas are integrated into ControlState by the engine

What SignalEvaluator does NOT do:
- Detect stagnation (that's GovernanceEngine's job)
- Respond to stagnation (that's GovernanceEngine's job)
- Clip or bound states (ControlState is unbounded)
- Learn or adapt (coefficients are fixed)

Assumptions:
- Output must produce deltas for all 5 canonical control axes
- Deltas are additive (integrated via ControlState.integrate())

Invariants:
- Deterministic: same inputs → same outputs
- Pure: no side effects
- Stateless: no internal state
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict
from governance.state import ControlState


class SignalEvaluator:
    """
    Signal evaluator that converts observations into control state deltas.
    
    This is the input layer of the governance engine. It translates 
    environmental signals into internal state changes.
    
    Boundary clarification:
    - Evaluation produces state DELTAS (not absolute values)
    - Evaluation does NOT detect stagnation (that's GovernanceEngine's job)
    - Evaluation does NOT respond to stagnation (that's GovernanceEngine's job)
    
    Preconditions:
    - All input signals in [0.0, 1.0]
    
    Postconditions:
    - Returns ControlState with delta values
    """
    
    def evaluate(self, stimulus: Dict[str, float]) -> Dict[str, float]:
        """
        Internal evaluation from raw stimulus dict.
        
        Args:
            stimulus: Dict with keys: novelty, difficulty, progress, urgency
            
        Returns:
            Dict of delta values for each control axis
        """
        n = stimulus.get("novelty", 0.0)
        d = stimulus.get("difficulty", 0.0)
        p = stimulus.get("progress", 0.0)
        u = stimulus.get("urgency", 0.0)
        t = stimulus.get("trust", 1.0)
        
        # Trust-Gating (Hardening)
        # We dampen positive signals (progress, novelty) by trust.
        # We DO NOT dampen negative signals (difficulty, urgency) to ensure fail-closed behavior.
        p_effective = p * t
        n_effective = n * t
        
        deltas = {
            "control_margin": (p_effective * 0.3) - (d * 0.1),
            "control_loss": (0.0 if p_effective > 0 else d * 0.4) + (u * 0.2),
            "exploration_pressure": (n_effective * 0.5) - ((1.0 - n_effective) * 0.2),
            "urgency_level": u * 0.6,
            "risk": -abs(p_effective) * 0.3,
        }
        return deltas

    def compute(self, reward: float, novelty: float, urgency: float, difficulty: float = 0.1, trust: float = 1.0) -> ControlState:
        """
        Compute control state delta from engine signals.
        
        Args:
            reward: Progress signal [0.0, 1.0]
            novelty: Novelty signal [0.0, 1.0]
            urgency: Urgency signal [0.0, 1.0]
            difficulty: Difficulty signal [0.0, 1.0]
        
        Returns:
            ControlState containing delta values (not absolute states).
            This is passed directly to ControlState.integrate().
            
        Postconditions:
        - Returns immutable ControlState
        - No side effects
        """
        stimulus = {
            "progress": reward,  # Mapping reward to progress
            "novelty": novelty,
            "urgency": urgency,
            "difficulty": difficulty,
            "trust": trust,
        }
        deltas = self.evaluate(stimulus)
        return ControlState(
            control_margin=deltas["control_margin"],
            control_loss=deltas["control_loss"],
            exploration_pressure=deltas["exploration_pressure"],
            urgency_level=deltas["urgency_level"],
            risk=deltas["risk"],
        )


# Backward compatibility aliases (deprecated)
AppraisalEngine = SignalEvaluator
