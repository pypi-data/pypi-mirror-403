"""
Integration test for the observe() API.

This tests the full extraction pipeline:
  Observation -> Extractor -> Validator -> Governance -> StepResult
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from governance.interface import observe
from governance.agent import EmoCoreAgent
from governance.observation import Observation
from governance.modes import Mode


class TestObserveAPI:
    """Integration tests for the observe() API."""

    def test_observe_success_increases_budget(self):
        """Successful observations should maintain healthy budget."""
        agent = EmoCoreAgent()
        
        obs = Observation(
            action="read_file",
            result="success",
            env_state_delta=0.3,
            agent_state_delta=0.1,
            elapsed_time=1.0
        )
        
        result = observe(agent, obs)
        
        assert result.halted is False
        assert result.mode == Mode.IDLE
        assert result.budget.effort > 0.5
        
    def test_observe_failure_streak_causes_halt(self):
        """Repeated failures should eventually cause a halt."""
        agent = EmoCoreAgent()
        
        obs = Observation(
            action="call_api",
            result="failure",
            env_state_delta=0.0,
            agent_state_delta=0.1,
            elapsed_time=1.0
        )
        
        halted = False
        for i in range(50):
            result = observe(agent, obs)
            if result.halted:
                halted = True
                break
        
        assert halted, "Agent should halt after repeated failures"
        
    def test_observe_stagnation_causes_halt(self):
        """Stagnation (success with no state change) should cause halt."""
        agent = EmoCoreAgent()
        
        # "Success" but nothing actually changes
        obs = Observation(
            action="think",
            result="success",
            env_state_delta=0.0,
            agent_state_delta=0.0,
            elapsed_time=1.0
        )
        
        halted = False
        for i in range(50):
            result = observe(agent, obs)
            if result.halted:
                halted = True
                break
        
        assert halted, "Agent should halt after stagnation"
        
    def test_observe_returns_control_log(self):
        """Observe should return control log for debugging."""
        agent = EmoCoreAgent()
        
        obs = Observation(
            action="test",
            result="success",
            env_state_delta=0.2,
            agent_state_delta=0.1,
            elapsed_time=1.0
        )
        
        result = observe(agent, obs)
        
        assert result.control_log is not None
        assert "control_loss" in result.control_log
        assert "control_margin" in result.control_log
