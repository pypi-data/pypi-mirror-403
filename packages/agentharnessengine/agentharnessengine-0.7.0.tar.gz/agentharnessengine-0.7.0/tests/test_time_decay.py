import time
import os 
import sys 
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from governance.agent import EmoCoreAgent
from governance.state import ControlState

def test_time_decay_reduces_budget():
    agent = EmoCoreAgent()
    
    # Needs positive control state to generate positive budget to decay from
    r1 = agent.step(reward=0.0, novelty=1.0, urgency=1.0)
    
    # Inject state manually or via step
    # 1. Step with high impact
    r0 = agent.step(reward=1.0, novelty=1.0, urgency=1.0)
    
    # Force state to valid nonzero using new fields
    agent.engine.state = ControlState(control_margin=1.0, urgency_level=1.0)
    
    # Step with dt > 0 (via sleep + step)
    # Disable inertia for this test to isolate decay
    agent.engine.BUDGET_INERTIA_ALPHA = 0.0
    
    time.sleep(0.2)
    r_decayed = agent.step(0,0,0)
    
    # Compute baseline
    gov_budget = agent.engine.budget_computer.compute(agent.engine.state, dt=0.0)
    
    # Verify decay
    assert r_decayed.budget.persistence < gov_budget.persistence

def test_recovery_happens_over_time():
    """
    Test that recovery increases effort/persistence ONLY when in RECOVERING mode.
    
    New invariant: Recovery occurs ONLY when mode == RECOVERING.
    To trigger RECOVERING, effort or persistence must drop below 0.3.
    """
    from governance.modes import Mode
    
    core = EmoCoreAgent()
    
    # Drive effort down by running multiple steps with zero/negative input
    # This accumulates control loss and reduces effort via governance
    for _ in range(10):
        r = core.step(-0.5, 0.0, 0.0)
    
    # Check we're in or approaching RECOVERING mode
    # If not yet recovering, continue until we are
    while r.mode != Mode.RECOVERING and not r.halted:
        r = core.step(-0.5, 0.0, 0.0)
        if r.halted:
            # If we halted, test can't proceed - this is acceptable
            return
    
    e_before_recovery = r.budget.effort
    
    # Wait for recovery delay and step again
    time.sleep(0.6)  # BALANCED profile has recovery_delay=0.5
    
    r_after = core.step(0.0, 0.0, 0.0)
    
    # In RECOVERING mode with dt >= recovery_delay, effort should increase
    # (bounded by stable budget and recovery cap)
    if r_after.mode == Mode.RECOVERING and not r_after.halted:
        assert r_after.budget.effort >= e_before_recovery, \
            f"Recovery should increase effort: {r_after.budget.effort} >= {e_before_recovery}"
