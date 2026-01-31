# src/governance/metrics.py
"""
Governance Metrics: Observability layer for the Governance Kernel.

This module provides:
- GovernanceMetrics: Immutable snapshot of kernel state
- MetricsCollector: Aggregates metrics over time
- Export formats: Prometheus text, JSONL

Usage:
    from governance.metrics import MetricsCollector
    
    collector = MetricsCollector()
    kernel = GovernanceKernel(profile)
    
    # After each step
    result = kernel.step(...)
    collector.record(result, signals)
    
    # Export
    print(collector.to_prometheus())
    collector.to_jsonl("metrics.jsonl")
"""
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import List, Callable, Optional, Dict, Any
from governance.result import EngineResult
from governance.signals import Signals


@dataclass(frozen=True)
class GovernanceMetrics:
    """
    Immutable snapshot of governance state at a single step.
    
    This is the canonical observability object. It captures everything
    needed to understand what the kernel decided and why.
    """
    # Temporal
    timestamp: str
    step: int
    
    # Budget (Output)
    effort: float
    risk: float
    exploration: float
    persistence: float
    
    # Control State (Internal)
    control_margin: float
    control_loss: float
    exploration_pressure: float
    urgency_level: float
    state_risk: float
    
    # Signals (Input)
    reward: float
    novelty: float
    urgency: float
    difficulty: float
    trust: float
    
    # Decision
    mode: str
    halted: bool
    failure_type: Optional[str] = None
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class MetricsCollector:
    """
    Collects and aggregates governance metrics over time.
    
    Features:
    - Records metrics from EngineResult + Signals
    - Supports hooks for real-time streaming
    - Exports to Prometheus and JSONL formats
    """
    
    def __init__(self):
        self._history: List[GovernanceMetrics] = []
        self._hooks: List[Callable[[GovernanceMetrics], None]] = []
        self._step_count = 0
    
    def add_hook(self, hook: Callable[[GovernanceMetrics], None]) -> None:
        """
        Register a callback to be invoked on each metric record.
        
        Args:
            hook: Function that receives GovernanceMetrics
        """
        self._hooks.append(hook)
    
    def remove_hook(self, hook: Callable[[GovernanceMetrics], None]) -> None:
        """Remove a previously registered hook."""
        if hook in self._hooks:
            self._hooks.remove(hook)
    
    def record(
        self,
        result: EngineResult,
        signals: Optional[Signals] = None,
        reward: float = 0.0,
        novelty: float = 0.0,
        urgency: float = 0.0,
        difficulty: float = 0.0,
        trust: float = 1.0,
    ) -> GovernanceMetrics:
        """
        Record metrics from a kernel step result.
        
        Args:
            result: The EngineResult from kernel.step()
            signals: Optional Signals object (if using observe())
            reward/novelty/urgency/difficulty/trust: Direct signal values
            
        Returns:
            The recorded GovernanceMetrics snapshot
        """
        self._step_count += 1
        
        # Extract signal values
        if signals is not None:
            reward = signals.reward
            novelty = signals.novelty
            urgency = signals.urgency
            difficulty = getattr(signals, 'difficulty', 0.0)
            trust = getattr(signals, 'trust', 1.0)
        
        # Build metrics snapshot
        metrics = GovernanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            step=self._step_count,
            # Budget
            effort=result.budget.effort,
            risk=result.budget.risk,
            exploration=result.budget.exploration,
            persistence=result.budget.persistence,
            # Control State (handle both dict and object)
            control_margin=result.state['control_margin'] if isinstance(result.state, dict) else result.state.control_margin,
            control_loss=result.state['control_loss'] if isinstance(result.state, dict) else result.state.control_loss,
            exploration_pressure=result.state['exploration_pressure'] if isinstance(result.state, dict) else result.state.exploration_pressure,
            urgency_level=result.state['urgency_level'] if isinstance(result.state, dict) else result.state.urgency_level,
            state_risk=result.state['risk'] if isinstance(result.state, dict) else result.state.risk,
            # Signals
            reward=reward,
            novelty=novelty,
            urgency=urgency,
            difficulty=difficulty,
            trust=trust,
            # Decision
            mode=result.mode.name if hasattr(result.mode, 'name') else str(result.mode),
            halted=result.halted,
            failure_type=result.failure.name if result.failure and hasattr(result.failure, 'name') else None,
            failure_reason=result.reason,
        )
        
        self._history.append(metrics)
        
        # Invoke hooks
        for hook in self._hooks:
            try:
                hook(metrics)
            except Exception:
                pass  # Don't let hook errors break collection
        
        return metrics
    
    @property
    def history(self) -> List[GovernanceMetrics]:
        """Get all recorded metrics."""
        return list(self._history)
    
    @property
    def latest(self) -> Optional[GovernanceMetrics]:
        """Get the most recent metrics snapshot."""
        return self._history[-1] if self._history else None
    
    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._history.clear()
        self._step_count = 0
    
    def to_prometheus(self) -> str:
        """
        Export latest metrics in Prometheus text format.
        
        Returns:
            Prometheus-compatible metrics string
        """
        if not self._history:
            return ""
        
        m = self._history[-1]
        lines = [
            "# HELP governance_budget_effort Current effort budget [0,1]",
            "# TYPE governance_budget_effort gauge",
            f"governance_budget_effort {m.effort:.4f}",
            "",
            "# HELP governance_budget_risk Current risk budget [0,1]",
            "# TYPE governance_budget_risk gauge",
            f"governance_budget_risk {m.risk:.4f}",
            "",
            "# HELP governance_budget_exploration Current exploration budget [0,1]",
            "# TYPE governance_budget_exploration gauge",
            f"governance_budget_exploration {m.exploration:.4f}",
            "",
            "# HELP governance_budget_persistence Current persistence budget [0,1]",
            "# TYPE governance_budget_persistence gauge",
            f"governance_budget_persistence {m.persistence:.4f}",
            "",
            "# HELP governance_control_margin Internal control margin",
            "# TYPE governance_control_margin gauge",
            f"governance_control_margin {m.control_margin:.4f}",
            "",
            "# HELP governance_control_loss Accumulated control loss (frustration)",
            "# TYPE governance_control_loss gauge",
            f"governance_control_loss {m.control_loss:.4f}",
            "",
            "# HELP governance_step_count Total steps executed",
            "# TYPE governance_step_count counter",
            f"governance_step_count {m.step}",
            "",
            "# HELP governance_halted Whether the kernel is halted (0/1)",
            "# TYPE governance_halted gauge",
            f"governance_halted {1 if m.halted else 0}",
        ]
        return "\n".join(lines)
    
    def to_jsonl(self, filepath: Optional[str] = None) -> str:
        """
        Export all metrics as JSON Lines.
        
        Args:
            filepath: If provided, write to file. Otherwise return string.
            
        Returns:
            JSONL string if no filepath given
        """
        lines = [m.to_json() for m in self._history]
        content = "\n".join(lines)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(content)
        
        return content
    
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Returns:
            Dict with min/max/avg for key metrics
        """
        if not self._history:
            return {}
        
        efforts = [m.effort for m in self._history]
        risks = [m.risk for m in self._history]
        losses = [m.control_loss for m in self._history]
        
        return {
            "total_steps": len(self._history),
            "halted": self._history[-1].halted,
            "final_mode": self._history[-1].mode,
            "effort": {
                "min": min(efforts),
                "max": max(efforts),
                "avg": sum(efforts) / len(efforts),
                "final": efforts[-1],
            },
            "risk": {
                "min": min(risks),
                "max": max(risks),
                "avg": sum(risks) / len(risks),
                "final": risks[-1],
            },
            "control_loss": {
                "min": min(losses),
                "max": max(losses),
                "final": losses[-1],
            },
        }
