#!/usr/bin/env python3
"""
Tests for the governance metrics module.
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from governance import EmoCoreAgent, step, Signals, PROFILES, ProfileType
from governance.metrics import GovernanceMetrics, MetricsCollector


class TestGovernanceMetrics:
    """Tests for GovernanceMetrics dataclass."""
    
    def test_metrics_is_immutable(self):
        """GovernanceMetrics should be frozen."""
        metrics = GovernanceMetrics(
            timestamp="2026-01-30T12:00:00Z",
            step=1,
            effort=0.5,
            risk=0.3,
            exploration=0.2,
            persistence=0.4,
            control_margin=0.5,
            control_loss=0.1,
            exploration_pressure=0.2,
            urgency_level=0.3,
            state_risk=0.1,
            reward=0.5,
            novelty=0.2,
            urgency=0.3,
            difficulty=0.1,
            trust=1.0,
            mode="NOMINAL",
            halted=False,
        )
        
        with pytest.raises(AttributeError):
            metrics.effort = 0.9
    
    def test_to_dict(self):
        """to_dict should convert to dictionary."""
        metrics = GovernanceMetrics(
            timestamp="2026-01-30T12:00:00Z",
            step=1,
            effort=0.5,
            risk=0.3,
            exploration=0.2,
            persistence=0.4,
            control_margin=0.5,
            control_loss=0.1,
            exploration_pressure=0.2,
            urgency_level=0.3,
            state_risk=0.1,
            reward=0.5,
            novelty=0.2,
            urgency=0.3,
            difficulty=0.1,
            trust=1.0,
            mode="NOMINAL",
            halted=False,
        )
        
        d = metrics.to_dict()
        assert d["step"] == 1
        assert d["effort"] == 0.5
        assert d["mode"] == "NOMINAL"
    
    def test_to_json(self):
        """to_json should produce valid JSON."""
        metrics = GovernanceMetrics(
            timestamp="2026-01-30T12:00:00Z",
            step=1,
            effort=0.5,
            risk=0.3,
            exploration=0.2,
            persistence=0.4,
            control_margin=0.5,
            control_loss=0.1,
            exploration_pressure=0.2,
            urgency_level=0.3,
            state_risk=0.1,
            reward=0.5,
            novelty=0.2,
            urgency=0.3,
            difficulty=0.1,
            trust=1.0,
            mode="NOMINAL",
            halted=False,
        )
        
        json_str = metrics.to_json()
        parsed = json.loads(json_str)
        assert parsed["step"] == 1


class TestMetricsCollector:
    """Tests for MetricsCollector."""
    
    def test_record_metrics(self):
        """record() should capture metrics from EngineResult."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        signals = Signals(reward=0.5, novelty=0.2, urgency=0.3)
        result = step(agent, signals)
        
        metrics = collector.record(result, signals)
        
        assert metrics.step == 1
        assert metrics.reward == 0.5
        assert metrics.novelty == 0.2
        assert metrics.mode in ("NOMINAL", "IDLE")  # Mode depends on profile
    
    def test_history_accumulates(self):
        """Multiple records should accumulate in history."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        for i in range(5):
            signals = Signals(reward=0.3, novelty=0.1, urgency=0.2)
            result = step(agent, signals)
            collector.record(result, signals)
        
        assert len(collector.history) == 5
        assert collector.history[0].step == 1
        assert collector.history[4].step == 5
    
    def test_hooks_are_called(self):
        """Hooks should be invoked on each record."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        received = []
        collector.add_hook(lambda m: received.append(m))
        
        signals = Signals(reward=0.5, novelty=0.2, urgency=0.3)
        result = step(agent, signals)
        collector.record(result, signals)
        
        assert len(received) == 1
        assert received[0].step == 1
    
    def test_prometheus_export(self):
        """to_prometheus() should produce valid Prometheus format."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        signals = Signals(reward=0.5, novelty=0.2, urgency=0.3)
        result = step(agent, signals)
        collector.record(result, signals)
        
        prom = collector.to_prometheus()
        
        assert "governance_budget_effort" in prom
        assert "governance_budget_risk" in prom
        assert "governance_halted 0" in prom
        assert "# TYPE governance_step_count counter" in prom
    
    def test_jsonl_export(self):
        """to_jsonl() should produce valid JSONL."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        for i in range(3):
            signals = Signals(reward=0.3, novelty=0.1, urgency=0.2)
            result = step(agent, signals)
            collector.record(result, signals)
        
        jsonl = collector.to_jsonl()
        lines = jsonl.strip().split("\n")
        
        assert len(lines) == 3
        for line in lines:
            parsed = json.loads(line)
            assert "step" in parsed
            assert "effort" in parsed
    
    def test_summary(self):
        """summary() should provide aggregate statistics."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        for i in range(10):
            signals = Signals(reward=0.3, novelty=0.1, urgency=0.2)
            result = step(agent, signals)
            collector.record(result, signals)
        
        summary = collector.summary()
        
        assert summary["total_steps"] == 10
        assert "effort" in summary
        assert "min" in summary["effort"]
        assert "max" in summary["effort"]
        assert "avg" in summary["effort"]
    
    def test_clear(self):
        """clear() should reset history."""
        agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])
        collector = MetricsCollector()
        
        signals = Signals(reward=0.5, novelty=0.2, urgency=0.3)
        result = step(agent, signals)
        collector.record(result, signals)
        
        assert len(collector.history) == 1
        
        collector.clear()
        
        assert len(collector.history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
