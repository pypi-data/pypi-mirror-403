
import pytest
from governance.enforcement import InProcessEnforcer, EnforcementBlocked
from governance.result import EngineResult
from governance.behavior import BehaviorBudget
from governance.modes import Mode
from governance.failures import FailureType

def mock_action(x, y):
    return x + y

@pytest.fixture
def enforcer():
    return InProcessEnforcer()

def test_enforcement_allows_action(enforcer):
    """Test that allowed checks execute the action."""
    # Create an ALLOW decision (not halted)
    decision = EngineResult(
        state=None,
        budget=BehaviorBudget(1.0, 0.0, 1.0, 0.0),
        halted=False,
        failure=FailureType.NONE,
        reason=None,
        mode=Mode.IDLE
    )
    
    result = enforcer.enforce(decision, mock_action, 5, 3)
    assert result == 8

def test_enforcement_blocks_action(enforcer):
    """Test that halted checks raise EnforcementBlocked."""
    # Create a HALT decision
    decision = EngineResult(
        state=None,
        budget=BehaviorBudget(0.0, 0.0, 0.0, 0.0),
        halted=True,
        failure=FailureType.SAFETY,
        reason="test_halt",
        mode=Mode.HALTED
    )
    
    with pytest.raises(EnforcementBlocked) as excinfo:
        enforcer.enforce(decision, mock_action, 5, 3)
    
    assert "test_halt" in str(excinfo.value)
    assert excinfo.value.halt_reason == "test_halt"
    assert excinfo.value.decision_snapshot == decision
