"""
QUARANTINED: This module is deprecated and should not be used.

ConstraintEngine is broken and violates core governance invariants:
- Checks for values in [0, 1] but ControlState allows UNBOUNDED accumulation
- Uses snapshot() method that doesn't exist on ControlState
- Duplicates stagnation detection that belongs in GovernanceEngine

DO NOT USE THIS MODULE. It is preserved only for reference.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataclasses import dataclass
from typing import List
from governance.state import ControlState
from collections import deque

@dataclass(frozen=True)
class Violation:
    name: str
    description: str


class ConstraintEngine:
    """
    ⚠️ DEPRECATED: Do not use.
    
    This class is broken and violates EmoCore's unbounded state rule.
    Control values are NOT bounded to [0, 1] in EmoCore.
    
    This module is quarantined and preserved only for reference.
    """
    F_DOMINANCE = 0.75
    
    def validate_state(self, state: ControlState) -> List[Violation]:
        """DEPRECATED: Do not use."""
        violations = []
        
        # BROKEN: Assumes value is bounded, but ControlState has unbounded accumulation
        # This check is incorrect and should not be used
        # values = state.snapshot()  # snapshot() doesn't exist
        # for name, value in values.items():
        #     if value < 0.0 or value > 1.0:
        #         violations.append(...)
        
        # Check for control loss dominance
        if state.control_loss > self.F_DOMINANCE:
            violations.append(Violation(
                name="dominance_violation",
                description=f"Control loss {state.control_loss} exceeds dominance threshold {self.F_DOMINANCE}"
            ))
            
        return violations
        
    def __init__(self, window=10, epsilon=0.01):
        """DEPRECATED: Stagnation detection belongs in GovernanceEngine, not ConstraintEngine."""
        self.progress_history = deque(maxlen=window)
        self.window = window
        self.epsilon = epsilon
        
    def update_progress(self, delta: float):
        """DEPRECATED: Do not use."""
        self.progress_history.append(delta)
        
    def is_stagnating(self) -> bool:
        """DEPRECATED: Use GovernanceEngine's built-in stagnation detection instead."""
        if len(self.progress_history) < self.window:
            return False
        return sum(self.progress_history) <= self.epsilon
