
import pytest
from governance.kernel import GovernanceKernel
from governance.enforcement import InProcessEnforcer, EnforcementBlocked
from governance.audit import AuditLogger
from governance.profiles import PROFILES, ProfileType
from governance.signals import Signals

def safe_action():
    return "success"

def test_full_harness_loop():
    """
    Simulate the full Agent Harness loop:
    Kernel -> Audit -> Enforcement -> Action
    """
    # 1. Setup
    # Use conservative profile to trigger halt easily
    kernel = GovernanceKernel(PROFILES[ProfileType.CONSERVATIVE])
    enforcer = InProcessEnforcer()
    logger = AuditLogger()
    
    # 2. Execution Loop Simulation
    actions_taken = 0
    
    # Step 1: Normal execution
    signals = Signals(reward=0.1, novelty=0.1, urgency=0.0)
    decision = kernel.step(
        reward=signals.reward,
        novelty=signals.novelty,
        urgency=signals.urgency
    )
    
    # Audit BEFORE enforcement
    logger.log(
        step=1,
        action="safe_action",
        params={},
        signals=signals.__dict__,
        result=decision
    )
    
    # Enforce
    result = enforcer.enforce(decision, safe_action)
    assert result == "success"
    actions_taken += 1
    
    # Step 2: Trigger HALT (simulate massive risk)
    # We cheat and force the kernel state or send massive signals
    # Conservative profile has max_risk=0.3. Let's send difficulty=1.0 to spike risk.
    
    # We'll just pump risk until it halts
    for i in range(10):
        signals = Signals(reward=0.0, novelty=0.0, urgency=0.0, difficulty=1.0)
        decision = kernel.step(
            reward=signals.reward,
            novelty=signals.novelty,
            urgency=signals.urgency,
            difficulty=signals.difficulty
        )
        
        logger.log(
            step=2+i,
            action="risky_action",
            params={},
            signals=signals.__dict__,
            result=decision
        )
        
        if decision.halted:
            # Verify enforcement blocks it
            with pytest.raises(EnforcementBlocked) as exc:
                enforcer.enforce(decision, safe_action)
                assert exc.value.halt_reason == decision.reason
            break
        else:
            enforcer.enforce(decision, safe_action)
            actions_taken += 1
            
    assert decision.halted, "Kernel should have halted due to risk"
    
    # Verify Audit Trail
    dump = logger.dump()
    assert len(dump) > 1
    last_entry = dump[-1]
    assert last_entry['decision_halted'] is True
    assert last_entry['halt_reason'] == decision.reason
