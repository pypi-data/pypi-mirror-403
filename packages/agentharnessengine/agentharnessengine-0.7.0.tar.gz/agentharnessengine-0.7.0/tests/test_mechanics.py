import pytest
import numpy as np
import os; import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from governance.mechanics import GovernanceEngine
from governance.state import ControlState
from governance.behavior import BehaviorBudget

def test_governance_pure_function():
    gov = GovernanceEngine()
    state = ControlState(control_margin=1.0, control_loss=0.0)
    
    # First call
    budget1 = gov.compute(state)
    
    # Second call - same input -> same output
    budget2 = gov.compute(state)
    
    assert budget1 == budget2
    # Ensure it returns BehaviorBudget
    assert isinstance(budget1, BehaviorBudget)

def test_governance_no_momentum_but_accepts_metaparameters():
    gov = GovernanceEngine()
    state = ControlState()
    
    # NOW it SHOULD accept stagnating and dt
    # This previously raised TypeError. Now it should succeed.
    b = gov.compute(state, stagnating=True, dt=0.5)
    assert isinstance(b, BehaviorBudget)

def test_governance_control_loss_suppression():
    gov = GovernanceEngine()
    # High control loss should suppress exploration (based on old F_DOM rule)
    state = ControlState(control_loss=0.9, exploration_pressure=1.0)
    
    budget = gov.compute(state)
    
    assert budget.exploration == 0.0
