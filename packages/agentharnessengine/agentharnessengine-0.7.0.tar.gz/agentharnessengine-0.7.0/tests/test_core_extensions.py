import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from governance.agent import EmoCoreAgent
from governance.modes import Mode
from governance.failures import FailureType
from governance.state import ControlState


class TestResetFunctionality:
    """Tests for v0.7 reset() method."""

    def test_reset_clears_halted_state(self):
        """Agent can be reset after halting."""
        agent = EmoCoreAgent()
        
        # Force exhaustion by running many negative steps
        for _ in range(100):
            result = agent.step(reward=-1.0, novelty=0.0, urgency=0.5, difficulty=0.8)
            if result.halted:
                break
        
        assert result.halted is True
        
        # Reset and verify
        agent.reset(reason="test_recovery")
        
        # Next step should work normally
        result = agent.step(reward=0.5, novelty=0.3, urgency=0.1, difficulty=0.1)
        assert result.halted is False
        assert result.mode != Mode.HALTED
        
    def test_reset_restores_full_budget(self):
        """After reset, budget is restored to full capacity."""
        agent = EmoCoreAgent()
        
        # Deplete budget
        for _ in range(50):
            result = agent.step(reward=-0.5, novelty=0.0, urgency=0.3, difficulty=0.5)
            if result.halted:
                break
        
        agent.reset(reason="budget_restore_test")
        
        result = agent.step(reward=0.1, novelty=0.1, urgency=0.0, difficulty=0.0)
        
        # Budget should be near full values (inertia still applies: 0.8 * 1.0 = 0.8)
        assert result.budget.effort >= 0.8
        assert result.budget.persistence >= 0.8
        
    def test_reset_preserves_failure_type_none(self):
        """After reset, failure type is cleared."""
        agent = EmoCoreAgent()
        
        # Force a halt
        for _ in range(100):
            result = agent.step(reward=-1.0, novelty=0.0, urgency=0.8, difficulty=0.9)
            if result.halted:
                break
        
        assert result.failure != FailureType.NONE
        
        agent.reset(reason="clear_failure")
        
        result = agent.step(reward=0.5, novelty=0.1, urgency=0.0, difficulty=0.0)
        assert result.failure == FailureType.NONE
        
    def test_soft_reset_blocked_before_cooldown(self):
        """Reset on non-halted agent before cooldown should raise error."""
        agent = EmoCoreAgent()
        
        # Only 1 step - below cooldown threshold
        result = agent.step(reward=0.5, novelty=0.3, urgency=0.1, difficulty=0.1)
        assert result.halted is False
        
        # This should raise because we haven't hit the cooldown
        with pytest.raises(RuntimeError) as excinfo:
            agent.reset(reason="soft_reset_test")
        
        assert "Reset blocked" in str(excinfo.value)
        
    def test_soft_reset_allowed_after_cooldown(self):
        """Reset on non-halted agent after cooldown should work."""
        agent = EmoCoreAgent()
        
        # Run enough steps to pass cooldown
        for _ in range(6):
            result = agent.step(reward=0.5, novelty=0.3, urgency=0.1, difficulty=0.1)
        
        assert result.halted is False
        
        # This should work now
        agent.reset(reason="soft_reset_after_cooldown")
        
        result = agent.step(reward=0.5, novelty=0.3, urgency=0.1, difficulty=0.1)
        assert result.halted is False


class TestControlLog:
    """Tests for v0.7 control_log observability."""
    
    def test_control_log_populated(self):
        """EngineResult includes control_log with all 5 axes."""
        agent = EmoCoreAgent()
        
        result = agent.step(reward=0.5, novelty=0.3, urgency=0.2, difficulty=0.1)
        
        assert result.control_log is not None
        assert "control_margin" in result.control_log
        assert "control_loss" in result.control_log
        assert "exploration_pressure" in result.control_log
        assert "urgency_level" in result.control_log
        assert "risk" in result.control_log
        
    def test_control_log_changes_over_steps(self):
        """Control values should evolve between steps."""
        agent = EmoCoreAgent()
        
        r1 = agent.step(reward=0.5, novelty=0.3, urgency=0.0, difficulty=0.0)
        r2 = agent.step(reward=-0.5, novelty=0.0, urgency=0.5, difficulty=0.5)
        
        # Control loss should increase with negative reward and difficulty
        assert r2.control_log["control_loss"] > r1.control_log["control_loss"]
