# emocore/state.py
"""
ControlState: Canonical internal state representation for governance.

This is the core state that the governance engine tracks and updates.
All fields represent accumulated control-system metrics.

Fields:
- control_margin: Belief in ability to influence outcome (higher = more capable)
- control_loss: Accumulated stress from obstacles/failures (higher = worse)
- exploration_pressure: Drive to seek novel states
- urgency_level: General activation/energy from time pressure
- risk: Perceived danger or uncertainty

Properties:
- Unbounded (can exceed [0, 1])
- Non-decaying (never decrease on their own)
- Not directly controllable (only influenced by evaluation)

Invariants:
- Immutable (frozen dataclass)
- Pure integration (no side effects)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ControlState:
    """
    Canonical control state axes.

    These fields are REQUIRED by SignalEvaluator and GovernanceEngine.
    No component may add, remove, or rename axes without breaking core invariants.

    Preconditions:
    - All fields are float
    
    Postconditions:
    - State is immutable after creation
    
    This class is INTERNAL to core. External consumers receive snapshots
    via the public interface.
    """
    control_margin: float = 0.0
    control_loss: float = 0.0
    exploration_pressure: float = 0.0
    urgency_level: float = 0.0
    risk: float = 0.0

    def integrate(self, delta: "ControlState") -> "ControlState":
        """
        Pure integration of state deltas.
        
        Args:
            delta: A ControlState containing delta values to add.
        
        Returns:
            New ControlState with deltas integrated.
        
        Invariants:
        - No decay
        - No clipping
        - No recovery
        - No mutation
        
        Postconditions:
        - Returns new immutable ControlState
        - Original state unchanged
        """
        return ControlState(
            control_margin=self.control_margin + delta.control_margin,
            control_loss=self.control_loss + delta.control_loss,
            exploration_pressure=self.exploration_pressure + delta.exploration_pressure,
            urgency_level=self.urgency_level + delta.urgency_level,
            risk=self.risk + delta.risk,
        )


# Backward compatibility alias (deprecated)
PressureState = ControlState
