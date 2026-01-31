# src/governance/coordination.py
"""
Multi-Agent Coordination: System-level governance for agent swarms.

This module provides:
- SharedBudgetPool: Resource allocation across agents
- AgentRegistry: Track active agents
- CascadeDetector: Detect runaway agent chains
- SystemGovernor: System-wide halt and health monitoring

Usage:
    from governance.coordination import SystemGovernor, SharedBudgetPool
    
    # Create system governor
    governor = SystemGovernor()
    
    # Register agents
    governor.register_agent("agent-1", kernel1)
    governor.register_agent("agent-2", kernel2)
    
    # Check system health
    status = governor.evaluate()
    if status.should_halt_all:
        governor.halt_all("Cascade detected")
"""
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
from governance.behavior import BehaviorBudget


class SystemStatus(Enum):
    """Overall system health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    HALTED = "halted"


@dataclass
class AgentState:
    """Snapshot of an agent's current state."""
    agent_id: str
    registered_at: str
    last_step_at: Optional[str] = None
    step_count: int = 0
    halted: bool = False
    budget: Optional[BehaviorBudget] = None
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)


@dataclass
class SystemHealthReport:
    """System-wide health report."""
    status: SystemStatus
    total_agents: int
    active_agents: int
    halted_agents: int
    cascade_depth: int
    total_steps: int
    should_halt_all: bool
    halt_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "halted_agents": self.halted_agents,
            "cascade_depth": self.cascade_depth,
            "total_steps": self.total_steps,
            "should_halt_all": self.should_halt_all,
            "halt_reason": self.halt_reason,
            "warnings": self.warnings,
        }


class SharedBudgetPool:
    """
    Shared budget pool across multiple agents.
    
    Provides fair allocation and prevents any single agent
    from consuming all resources.
    """
    
    def __init__(
        self,
        total_effort: float = 10.0,
        total_risk: float = 5.0,
        max_per_agent_effort: float = 2.0,
        max_per_agent_risk: float = 1.0,
    ):
        """
        Args:
            total_effort: Total effort budget for all agents
            total_risk: Total risk budget for all agents
            max_per_agent_effort: Max effort any single agent can allocate
            max_per_agent_risk: Max risk any single agent can allocate
        """
        self._total_effort = total_effort
        self._total_risk = total_risk
        self._max_effort = max_per_agent_effort
        self._max_risk = max_per_agent_risk
        
        self._allocated_effort: Dict[str, float] = {}
        self._allocated_risk: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def allocate(
        self,
        agent_id: str,
        effort: float = 1.0,
        risk: float = 0.5,
    ) -> bool:
        """
        Allocate budget to an agent.
        
        Args:
            agent_id: Unique agent identifier
            effort: Requested effort budget
            risk: Requested risk budget
            
        Returns:
            True if allocation succeeded, False if insufficient budget
        """
        with self._lock:
            # Clamp to per-agent limits
            effort = min(effort, self._max_effort)
            risk = min(risk, self._max_risk)
            
            # Check available
            used_effort = sum(self._allocated_effort.values())
            used_risk = sum(self._allocated_risk.values())
            
            if used_effort + effort > self._total_effort:
                return False
            if used_risk + risk > self._total_risk:
                return False
            
            # Allocate
            self._allocated_effort[agent_id] = effort
            self._allocated_risk[agent_id] = risk
            return True
    
    def release(self, agent_id: str) -> None:
        """Release budget allocated to an agent."""
        with self._lock:
            self._allocated_effort.pop(agent_id, None)
            self._allocated_risk.pop(agent_id, None)
    
    def get_allocated(self, agent_id: str) -> tuple:
        """Get budget allocated to an agent."""
        with self._lock:
            return (
                self._allocated_effort.get(agent_id, 0.0),
                self._allocated_risk.get(agent_id, 0.0)
            )
    
    def get_remaining(self) -> tuple:
        """Get remaining budget in the pool."""
        with self._lock:
            used_effort = sum(self._allocated_effort.values())
            used_risk = sum(self._allocated_risk.values())
            return (
                self._total_effort - used_effort,
                self._total_risk - used_risk
            )
    
    def get_utilization(self) -> Dict[str, float]:
        """Get pool utilization percentages."""
        with self._lock:
            used_effort = sum(self._allocated_effort.values())
            used_risk = sum(self._allocated_risk.values())
            return {
                "effort_utilization": used_effort / self._total_effort if self._total_effort > 0 else 0,
                "risk_utilization": used_risk / self._total_risk if self._total_risk > 0 else 0,
                "total_allocations": len(self._allocated_effort),
            }


class CascadeDetector:
    """
    Detect runaway agent cascade chains.
    
    A cascade occurs when agents spawn too many child agents
    or the call depth exceeds safe limits.
    """
    
    def __init__(
        self,
        max_depth: int = 5,
        max_children_per_agent: int = 10,
        max_total_agents: int = 100,
    ):
        """
        Args:
            max_depth: Maximum agent call depth
            max_children_per_agent: Max children a single agent can spawn
            max_total_agents: Max total agents in system
        """
        self._max_depth = max_depth
        self._max_children = max_children_per_agent
        self._max_total = max_total_agents
        
        self._parent_map: Dict[str, Optional[str]] = {}
        self._children_map: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
    
    def register_spawn(self, parent_id: Optional[str], child_id: str) -> bool:
        """
        Register an agent spawn event.
        
        Args:
            parent_id: ID of spawning agent (None for root)
            child_id: ID of spawned agent
            
        Returns:
            True if spawn allowed, False if cascade limit reached
        """
        with self._lock:
            # Check total agents
            if len(self._parent_map) >= self._max_total:
                return False
            
            # Check children limit
            if parent_id:
                children = self._children_map.get(parent_id, [])
                if len(children) >= self._max_children:
                    return False
            
            # Check depth
            depth = self._get_depth(parent_id)
            if depth >= self._max_depth:
                return False
            
            # Register
            self._parent_map[child_id] = parent_id
            if parent_id:
                if parent_id not in self._children_map:
                    self._children_map[parent_id] = []
                self._children_map[parent_id].append(child_id)
            
            return True
    
    def unregister(self, agent_id: str) -> None:
        """Remove an agent from tracking."""
        with self._lock:
            parent = self._parent_map.pop(agent_id, None)
            if parent and parent in self._children_map:
                self._children_map[parent] = [
                    c for c in self._children_map[parent] if c != agent_id
                ]
            self._children_map.pop(agent_id, None)
    
    def get_depth(self, agent_id: str) -> int:
        """Get the depth of an agent in the hierarchy."""
        with self._lock:
            return self._get_depth(agent_id)
    
    def _get_depth(self, agent_id: Optional[str]) -> int:
        """Internal depth calculation (no lock)."""
        depth = 0
        current = agent_id
        while current:
            depth += 1
            current = self._parent_map.get(current)
        return depth
    
    def get_max_current_depth(self) -> int:
        """Get the maximum depth of any agent currently registered."""
        with self._lock:
            if not self._parent_map:
                return 0
            return max(self._get_depth(aid) for aid in self._parent_map.keys())
    
    def check_cascade_risk(self) -> Dict[str, Any]:
        """Check current cascade risk metrics."""
        with self._lock:
            max_depth = 0
            max_children = 0
            
            for aid in self._parent_map.keys():
                depth = self._get_depth(aid)
                max_depth = max(max_depth, depth)
            
            for children in self._children_map.values():
                max_children = max(max_children, len(children))
            
            return {
                "current_agents": len(self._parent_map),
                "max_depth": max_depth,
                "max_children": max_children,
                "depth_risk": max_depth / self._max_depth,
                "agent_risk": len(self._parent_map) / self._max_total,
            }


class AgentRegistry:
    """
    Registry of all active agents in the system.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentState] = {}
        self._lock = threading.Lock()
    
    def register(
        self,
        agent_id: str,
        parent_id: Optional[str] = None,
    ) -> AgentState:
        """Register a new agent."""
        with self._lock:
            state = AgentState(
                agent_id=agent_id,
                registered_at=datetime.now(timezone.utc).isoformat(),
                parent_id=parent_id,
            )
            self._agents[agent_id] = state
            
            # Update parent's children list
            if parent_id and parent_id in self._agents:
                self._agents[parent_id].children.append(agent_id)
            
            return state
    
    def unregister(self, agent_id: str) -> None:
        """Remove an agent from registry."""
        with self._lock:
            state = self._agents.pop(agent_id, None)
            if state and state.parent_id and state.parent_id in self._agents:
                parent = self._agents[state.parent_id]
                parent.children = [c for c in parent.children if c != agent_id]
    
    def update_step(
        self,
        agent_id: str,
        budget: Optional[BehaviorBudget] = None,
        halted: bool = False,
    ) -> None:
        """Update agent after a step."""
        with self._lock:
            if agent_id in self._agents:
                state = self._agents[agent_id]
                state.last_step_at = datetime.now(timezone.utc).isoformat()
                state.step_count += 1
                state.halted = halted
                if budget:
                    state.budget = budget
    
    def get(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state."""
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_all(self) -> List[AgentState]:
        """Get all agent states."""
        with self._lock:
            return list(self._agents.values())
    
    def get_active(self) -> List[AgentState]:
        """Get non-halted agents."""
        with self._lock:
            return [a for a in self._agents.values() if not a.halted]
    
    def get_halted(self) -> List[AgentState]:
        """Get halted agents."""
        with self._lock:
            return [a for a in self._agents.values() if a.halted]


class SystemGovernor:
    """
    System-wide governor for multi-agent governance.
    
    Coordinates shared budgets, cascade detection, and system-level halts.
    """
    
    def __init__(
        self,
        budget_pool: Optional[SharedBudgetPool] = None,
        cascade_detector: Optional[CascadeDetector] = None,
        max_total_steps: int = 10000,
        halt_on_cascade: bool = True,
    ):
        """
        Args:
            budget_pool: Shared budget pool (creates default if None)
            cascade_detector: Cascade detector (creates default if None)
            max_total_steps: Max steps across all agents
            halt_on_cascade: Auto-halt all if cascade detected
        """
        self._budget_pool = budget_pool or SharedBudgetPool()
        self._cascade = cascade_detector or CascadeDetector()
        self._registry = AgentRegistry()
        self._max_total_steps = max_total_steps
        self._halt_on_cascade = halt_on_cascade
        
        self._system_halted = False
        self._halt_reason: Optional[str] = None
        self._halt_hooks: List[Callable[[str], None]] = []
        self._lock = threading.Lock()
    
    def register_agent(
        self,
        agent_id: str,
        parent_id: Optional[str] = None,
        effort: float = 1.0,
        risk: float = 0.5,
    ) -> bool:
        """
        Register a new agent with the system.
        
        Returns:
            True if registration succeeded
        """
        with self._lock:
            if self._system_halted:
                return False
            
            # Check cascade
            if not self._cascade.register_spawn(parent_id, agent_id):
                if self._halt_on_cascade:
                    self._system_halt_internal("Cascade limit exceeded")
                return False
            
            # Allocate budget
            if not self._budget_pool.allocate(agent_id, effort, risk):
                self._cascade.unregister(agent_id)
                return False
            
            # Register
            self._registry.register(agent_id, parent_id)
            return True
    
    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the system."""
        with self._lock:
            self._registry.unregister(agent_id)
            self._cascade.unregister(agent_id)
            self._budget_pool.release(agent_id)
    
    def report_step(
        self,
        agent_id: str,
        budget: Optional[BehaviorBudget] = None,
        halted: bool = False,
    ) -> None:
        """Report that an agent completed a step."""
        self._registry.update_step(agent_id, budget, halted)
    
    def add_halt_hook(self, hook: Callable[[str], None]) -> None:
        """Add a callback for system-wide halt events."""
        self._halt_hooks.append(hook)
    
    def halt_all(self, reason: str) -> None:
        """Halt all agents in the system."""
        with self._lock:
            self._system_halt_internal(reason)
    
    def _system_halt_internal(self, reason: str) -> None:
        """Internal halt (assumes lock held)."""
        self._system_halted = True
        self._halt_reason = reason
        
        # Mark all agents as halted
        for state in self._registry.get_all():
            state.halted = True
        
        # Fire hooks (release lock first)
        hooks = list(self._halt_hooks)
        # Note: In production, fire hooks outside lock
        for hook in hooks:
            try:
                hook(reason)
            except Exception:
                pass
    
    def evaluate(self) -> SystemHealthReport:
        """
        Evaluate system health.
        
        Returns:
            SystemHealthReport with current status
        """
        with self._lock:
            agents = self._registry.get_all()
            active = [a for a in agents if not a.halted]
            halted = [a for a in agents if a.halted]
            
            total_steps = sum(a.step_count for a in agents)
            cascade_depth = self._cascade.get_max_current_depth()
            cascade_risk = self._cascade.check_cascade_risk()
            
            warnings = []
            should_halt = False
            halt_reason = None
            
            # Check system halt
            if self._system_halted:
                return SystemHealthReport(
                    status=SystemStatus.HALTED,
                    total_agents=len(agents),
                    active_agents=0,
                    halted_agents=len(agents),
                    cascade_depth=cascade_depth,
                    total_steps=total_steps,
                    should_halt_all=False,
                    halt_reason=self._halt_reason,
                )
            
            # Check total steps
            if total_steps >= self._max_total_steps:
                should_halt = True
                halt_reason = f"Total steps ({total_steps}) exceeded limit"
            
            # Check cascade risk
            if cascade_risk["depth_risk"] >= 1.0:
                should_halt = True
                halt_reason = "Cascade depth limit reached"
            elif cascade_risk["depth_risk"] >= 0.8:
                warnings.append(f"High cascade depth: {cascade_risk['max_depth']}")
            
            if cascade_risk["agent_risk"] >= 1.0:
                should_halt = True
                halt_reason = "Agent count limit reached"
            elif cascade_risk["agent_risk"] >= 0.8:
                warnings.append(f"High agent count: {cascade_risk['current_agents']}")
            
            # Determine status
            if should_halt:
                status = SystemStatus.CRITICAL
            elif warnings:
                status = SystemStatus.DEGRADED
            elif len(halted) > len(active):
                status = SystemStatus.DEGRADED
            else:
                status = SystemStatus.HEALTHY
            
            return SystemHealthReport(
                status=status,
                total_agents=len(agents),
                active_agents=len(active),
                halted_agents=len(halted),
                cascade_depth=cascade_depth,
                total_steps=total_steps,
                should_halt_all=should_halt,
                halt_reason=halt_reason,
                warnings=warnings,
            )
    
    @property
    def is_halted(self) -> bool:
        """Check if system is halted."""
        return self._system_halted
    
    @property
    def budget_pool(self) -> SharedBudgetPool:
        """Get shared budget pool."""
        return self._budget_pool
    
    @property
    def registry(self) -> AgentRegistry:
        """Get agent registry."""
        return self._registry
