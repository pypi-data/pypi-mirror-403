#!/usr/bin/env python3
"""
Tests for the multi-agent coordination module.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from governance.coordination import (
    SharedBudgetPool, CascadeDetector, AgentRegistry, SystemGovernor,
    AgentState, SystemHealthReport, SystemStatus
)


class TestSharedBudgetPool:
    """Tests for SharedBudgetPool."""
    
    def test_allocate_success(self):
        """Should allocate budget when available."""
        pool = SharedBudgetPool(total_effort=10.0, total_risk=5.0)
        assert pool.allocate("agent-1", effort=2.0, risk=1.0)
        assert pool.get_allocated("agent-1") == (2.0, 1.0)
    
    def test_allocate_exceeds_total(self):
        """Should reject allocation when pool exhausted."""
        pool = SharedBudgetPool(total_effort=5.0, max_per_agent_effort=5.0)  # Allow full allocation
        assert pool.allocate("agent-1", effort=3.0)
        assert pool.allocate("agent-2", effort=2.0)
        assert not pool.allocate("agent-3", effort=1.0)  # Would exceed
    
    def test_allocate_per_agent_limit(self):
        """Should clamp to per-agent limit."""
        pool = SharedBudgetPool(total_effort=10.0, max_per_agent_effort=2.0)
        pool.allocate("agent-1", effort=5.0)  # Requests 5, clamped to 2
        assert pool.get_allocated("agent-1") == (2.0, 0.5)  # Default risk
    
    def test_release_budget(self):
        """Should release budget back to pool."""
        pool = SharedBudgetPool(total_effort=5.0, max_per_agent_effort=3.0)
        pool.allocate("agent-1", effort=3.0)
        remaining_after = pool.get_remaining()
        assert remaining_after[0] == 2.0  # 5 - 3 = 2
        
        pool.release("agent-1")
        assert pool.get_remaining() == (5.0, 5.0)
    
    def test_utilization(self):
        """Should track utilization correctly."""
        pool = SharedBudgetPool(total_effort=10.0, total_risk=5.0, max_per_agent_effort=5.0, max_per_agent_risk=2.5)
        pool.allocate("agent-1", effort=5.0, risk=2.5)
        
        util = pool.get_utilization()
        assert util["effort_utilization"] == 0.5
        assert util["risk_utilization"] == 0.5
        assert util["total_allocations"] == 1


class TestCascadeDetector:
    """Tests for CascadeDetector."""
    
    def test_register_root(self):
        """Should allow registering root agents."""
        detector = CascadeDetector(max_depth=5)
        assert detector.register_spawn(None, "root-1")
        assert detector.get_depth("root-1") == 1
    
    def test_register_chain(self):
        """Should track parent-child chains."""
        detector = CascadeDetector(max_depth=5)
        detector.register_spawn(None, "root")
        detector.register_spawn("root", "child-1")
        detector.register_spawn("child-1", "child-2")
        
        assert detector.get_depth("root") == 1
        assert detector.get_depth("child-1") == 2
        assert detector.get_depth("child-2") == 3
    
    def test_depth_limit(self):
        """Should block when depth limit reached."""
        detector = CascadeDetector(max_depth=3)
        detector.register_spawn(None, "a")
        detector.register_spawn("a", "b")
        detector.register_spawn("b", "c")
        assert not detector.register_spawn("c", "d")  # Depth 4 blocked
    
    def test_children_limit(self):
        """Should block when children limit reached."""
        detector = CascadeDetector(max_children_per_agent=2)
        detector.register_spawn(None, "parent")
        detector.register_spawn("parent", "c1")
        detector.register_spawn("parent", "c2")
        assert not detector.register_spawn("parent", "c3")  # 3rd child blocked
    
    def test_total_limit(self):
        """Should block when total agent limit reached."""
        detector = CascadeDetector(max_total_agents=3)
        detector.register_spawn(None, "a")
        detector.register_spawn(None, "b")
        detector.register_spawn(None, "c")
        assert not detector.register_spawn(None, "d")  # 4th blocked
    
    def test_cascade_risk(self):
        """Should report cascade risk metrics."""
        detector = CascadeDetector(max_depth=10, max_total_agents=100)
        detector.register_spawn(None, "a")
        detector.register_spawn("a", "b")
        
        risk = detector.check_cascade_risk()
        assert risk["current_agents"] == 2
        assert risk["max_depth"] == 2


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_register_agent(self):
        """Should register agents with state."""
        registry = AgentRegistry()
        state = registry.register("agent-1")
        
        assert state.agent_id == "agent-1"
        assert state.step_count == 0
        assert not state.halted
    
    def test_update_step(self):
        """Should update agent on step."""
        registry = AgentRegistry()
        registry.register("agent-1")
        registry.update_step("agent-1")
        
        state = registry.get("agent-1")
        assert state.step_count == 1
    
    def test_parent_child(self):
        """Should track parent-child relationships."""
        registry = AgentRegistry()
        registry.register("parent")
        registry.register("child", parent_id="parent")
        
        parent = registry.get("parent")
        assert "child" in parent.children
    
    def test_get_active_halted(self):
        """Should filter active vs halted agents."""
        registry = AgentRegistry()
        registry.register("a")
        registry.register("b")
        registry.update_step("b", halted=True)
        
        assert len(registry.get_active()) == 1
        assert len(registry.get_halted()) == 1


class TestSystemGovernor:
    """Tests for SystemGovernor."""
    
    def test_register_agent(self):
        """Should register agents and allocate budget."""
        governor = SystemGovernor()
        assert governor.register_agent("agent-1")
        
        state = governor.registry.get("agent-1")
        assert state is not None
    
    def test_register_blocked_when_halted(self):
        """Should block registration when system halted."""
        governor = SystemGovernor()
        governor.halt_all("Test halt")
        
        assert not governor.register_agent("agent-1")
    
    def test_cascade_triggers_halt(self):
        """Should halt system when cascade limit reached."""
        governor = SystemGovernor(
            cascade_detector=CascadeDetector(max_depth=2),
            halt_on_cascade=True
        )
        governor.register_agent("a")
        governor.register_agent("b", parent_id="a")
        governor.register_agent("c", parent_id="b")  # Exceeds depth
        
        assert governor.is_halted
    
    def test_evaluate_healthy(self):
        """Should report healthy status."""
        governor = SystemGovernor()
        governor.register_agent("agent-1")
        
        report = governor.evaluate()
        assert report.status == SystemStatus.HEALTHY
        assert report.total_agents == 1
    
    def test_evaluate_critical_on_step_limit(self):
        """Should report critical when step limit exceeded."""
        governor = SystemGovernor(max_total_steps=10)
        governor.register_agent("agent-1")
        
        for _ in range(15):
            governor.report_step("agent-1")
        
        report = governor.evaluate()
        assert report.should_halt_all
        assert "steps" in report.halt_reason.lower()
    
    def test_halt_hook(self):
        """Should fire halt hooks."""
        governor = SystemGovernor()
        called = []
        governor.add_halt_hook(lambda reason: called.append(reason))
        
        governor.halt_all("Test reason")
        
        assert len(called) == 1
        assert called[0] == "Test reason"
    
    def test_unregister_releases_resources(self):
        """Should release resources when agent unregistered."""
        governor = SystemGovernor()
        governor.register_agent("agent-1", effort=2.0)
        
        initial = governor.budget_pool.get_remaining()
        governor.unregister_agent("agent-1")
        final = governor.budget_pool.get_remaining()
        
        assert final[0] > initial[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
