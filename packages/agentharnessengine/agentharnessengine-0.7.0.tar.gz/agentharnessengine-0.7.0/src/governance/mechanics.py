# emocore/governance.py
"""
GovernanceEngine: Translates control state into behavioral permission.

What GovernanceEngine does:
- Converts ControlState into BehaviorBudget via matrix multiplication
- Applies profile-based scaling and decay
- Responds to stagnation signals from Engine
- Clips output to [0, 1] range

What GovernanceEngine does NOT do:
- Detect stagnation (that's the Engine's job)
- Decide when to halt (that's the Engine's job)
- Learn or optimize (matrices are fixed)
- Control actions (that's downstream enforcement)

Assumptions:
- ControlState has exactly 5 canonical axes in order:
  control_margin, control_loss, exploration_pressure, urgency_level, risk
- BehaviorBudget has exactly 4 dimensions: effort, risk, exploration, persistence
- W and V matrices are fixed

Invariants:
- Deterministic: same inputs → same outputs
- Stateless: no internal mutable state
- Pure: no side effects
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from dataclasses import dataclass
from typing import Optional
from governance.behavior import BehaviorBudget
from governance.state import ControlState


class GovernanceEngine:
    """
    Stateless governance engine that computes behavioral permission from control state.
    
    The governance equation is:
        g = W.T @ s - V.T @ s
    
    Where:
    - s is the control state vector [control_margin, control_loss, exploration_pressure, urgency_level, risk]
    - W is the enabling matrix (positive state → positive budget)
    - V is the suppressive matrix (control_loss suppresses all dimensions)
    - g is the raw governance output [effort, risk, exploration, persistence]
    
    This is NOT learning. The matrices are fixed.
    This is NOT optimization. The computation is deterministic.
    This is pure governance: state → permission.
    
    Boundary clarification:
    - Engine DETECTS stagnation and passes flag to governance
    - Governance RESPONDS to stagnation by scaling effort/persistence
    - Profiles TUNE the response via scaling and decay parameters
    
    Preconditions:
    - ControlState must have all 5 axes defined
    
    Postconditions:
    - Returns BehaviorBudget with values in [0.0, 1.0]
    """
    
    # Enabling matrix (control state → governance)
    # Rows: control state axes (control_margin, control_loss, exploration_pressure, urgency_level, risk)
    # Cols: budget dimensions (effort, risk, exploration, persistence)
    W = np.array([
        [0.6, 0.3, 0.2, 0.5],  # control_margin
        [0.0, 0.0, 0.0, 0.0],  # control_loss (no enabling)
        [0.2, 0.1, 0.7, 0.1],  # exploration_pressure
        [0.3, 0.2, 0.1, 0.2],  # urgency_level
        [0.1, 0.5, 0.3, 0.1],  # risk
    ])

    # Suppressive matrix (only control_loss suppresses)
    # Control loss suppresses all budget dimensions
    V = np.array([
        [0.0, 0.0, 0.0, 0.0],  # control_margin
        [0.7, 0.9, 0.9, 0.8],  # control_loss suppresses all
        [0.0, 0.0, 0.0, 0.0],  # exploration_pressure
        [0.0, 0.0, 0.0, 0.0],  # urgency_level
        [0.0, 0.0, 0.0, 0.0],  # risk
    ])

    def __init__(self, profile=None):
        self.profile = profile

    def compute(self, state: ControlState, stagnating: bool = False, dt: float = 0.0) -> BehaviorBudget:
        """
        Compute behavioral budget from control state.
        
        Args:
            state: Current ControlState
            stagnating: Whether the system is in stagnation
            dt: Time delta for decay calculations
            
        Returns:
            BehaviorBudget with values clamped to [0.0, 1.0]
            
        Invariants:
        - Pure function (no side effects)
        - Deterministic (same inputs → same outputs)
        """
        s = np.array([
            state.control_margin,
            state.control_loss,
            state.exploration_pressure,
            state.urgency_level,
            state.risk,
        ])

        g = self.W.T @ s - self.V.T @ s

        # 1. Stagnation Scaling
        # Applied to effort (index 0) and persistence (index 3)
        if stagnating and self.profile:
            g[0] *= self.profile.stagnation_effort_scale
            g[3] *= self.profile.stagnation_persistence_scale

        # 2. Profile Scaling
        if self.profile:
            g[0] *= self.profile.effort_scale
            g[1] *= self.profile.risk_scale
            g[2] *= self.profile.exploration_scale
            g[3] *= self.profile.persistence_scale

        # 3. Decay (Time + Step)
        if self.profile:
            decay_expl = self.profile.exploration_decay + dt * self.profile.time_exploration_decay
            decay_pers = self.profile.persistence_decay + dt * self.profile.time_persistence_decay
            
            g[2] -= decay_expl
            g[3] -= decay_pers

        # 4. Clip to valid range
        g = np.clip(g, 0.0, 1.0)

        return BehaviorBudget(
            effort=float(g[0]),
            risk=float(g[1]),
            exploration=float(g[2]),
            persistence=float(g[3]),
        )
