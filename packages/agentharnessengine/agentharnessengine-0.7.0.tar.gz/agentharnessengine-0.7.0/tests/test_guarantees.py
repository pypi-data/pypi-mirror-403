import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from governance.behavior import BehaviorBudget
from governance.state import PressureState
from governance.failures import FailureType
from governance.modes import Mode
from governance.guarantees import StepResult, GuaranteeEnforcer
def test_halted_zeroes_budget():
    result = StepResult(
        state=PressureState(),
        budget=BehaviorBudget(1, 1, 1, 1),
        halted=True,
        failure=FailureType.EXHAUSTION,
        reason="exhaustion",
        mode=Mode.IDLE,
    )

    enforced = GuaranteeEnforcer().enforce(result)

    assert enforced.budget.effort == 0.0
    assert enforced.halted is True
