import pytest
import os; import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from governance.state import ControlState

def test_state_immutable_integration():
    initial = ControlState()
    delta = ControlState(control_margin=0.1, control_loss=0.2)
    
    new_state = initial.integrate(delta)
    
    # Original should be unchanged
    assert initial.control_margin == 0.0
    assert initial.control_loss == 0.0
    
    # New state should have changes
    assert new_state.control_margin == 0.1
    assert new_state.control_loss == 0.2

def test_state_no_clipping_in_state():
    initial = ControlState(control_margin=0.9)
    # Even if we accumulate lots of margin, state just accumulates
    delta = ControlState(control_margin=0.5)
    new_state = initial.integrate(delta)
    assert new_state.control_margin == 1.4

def test_state_no_decay_method():
    initial = ControlState()
    # Ensure there is no decay method
    assert not hasattr(initial, "decay")
    assert not hasattr(initial, "momentum")
