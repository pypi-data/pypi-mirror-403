# Agent Harness Implementation Guide

This document maps the Agent Harness specification to concrete implementation components and code structures.

## Component Mapping (Spec → Code)

### 1. Signals System (Observations)

**Spec says:**
> Signals describe what happened. They are inputs to governance, not decisions.

**What you need to build:**

```python
# agentguard/signals/base.py
from dataclasses import dataclass
from typing import Protocol

class Signal(Protocol):
    """Base signal interface"""
    @property
    def value(self) -> float:
        """Normalized signal value [0.0, 1.0]"""
        ...
        
    @property
    def is_monotonic(self) -> bool:
        """Does this signal only increase?"""
        ...

# Four canonical signal classes
@dataclass
class EffortSignal(Signal):
    """Effort signals: steps, time, compute"""
    steps: int
    time_elapsed: float
    compute_consumed: float
    
    @property
    def value(self) -> float:
        # Combine into normalized effort signal
        return normalize(self.steps, self.time_elapsed, self.compute_consumed)

@dataclass
class ProgressSignal(Signal):
    """Progress signals: completion delta, novelty, repeated states"""
    completion_delta: float  # Change in task completion
    novelty: float           # New information gained
    state_repetitions: int   # How many times in same state
    
    @property
    def value(self) -> float:
        # Low progress = high repetition, low novelty
        if self.state_repetitions > 3:
            return 0.0
        return (self.completion_delta + self.novelty) / 2

@dataclass
class FailureSignal(Signal):
    """Failure signals: retries, errors, exceptions"""
    retry_count: int
    tool_errors: int
    exception_count: int
    
    @property
    def value(self) -> float:
        # High failure = high signal
        return min(1.0, (self.retry_count + self.tool_errors) / 10)

@dataclass
class RiskSignal(Signal):
    """Risk signals: action category, escalation, side effects"""
    action_category: str  # "read", "write", "delete", "admin"
    permission_level: int  # 0=read, 1=write, 2=admin
    has_side_effects: bool
    
    RISK_WEIGHTS = {
        "read": 0.1,
        "write": 0.5,
        "delete": 0.9,
        "admin": 1.0
    }
    
    @property
    def value(self) -> float:
        base_risk = self.RISK_WEIGHTS.get(self.action_category, 0.5)
        if self.has_side_effects:
            base_risk *= 1.5
        return min(1.0, base_risk)
```

**Key implementation rule:**
- Signals are **pure observations**
- No interpretation, no decisions
- Composable and testable in isolation

---

### 2. Budgets System (Limits)

**Spec says:**
> Budgets define what is allowed. Bounded, monotonically depleting, non-increasing, finite.

**What you need to build:**

```python
# agentguard/budgets/base.py
from dataclasses import dataclass
from typing import Protocol

class Budget(Protocol):
    """Base budget interface"""
    @property
    def remaining(self) -> float:
        """Budget remaining [0.0, 1.0]"""
        ...
        
    def deplete(self, amount: float) -> None:
        """Reduce budget (monotonic)"""
        ...
        
    @property
    def is_exhausted(self) -> bool:
        """Has budget hit zero?"""
        ...

@dataclass
class BudgetState:
    """Immutable budget snapshot"""
    effort: float      # [0.0, 1.0]
    persistence: float # [0.0, 1.0]
    risk: float        # [0.0, 1.0]
    exploration: float # [0.0, 1.0]
    
    def is_any_exhausted(self, threshold: float = 0.0) -> bool:
        """Check if any budget is depleted"""
        return (
            self.effort <= threshold or
            self.persistence <= threshold or
            self.risk <= threshold or
            self.exploration <= threshold
        )
    
    def deplete_effort(self, amount: float) -> 'BudgetState':
        """Return new state with depleted effort (immutable)"""
        return BudgetState(
            effort=max(0.0, self.effort - amount),
            persistence=self.persistence,
            risk=self.risk,
            exploration=self.exploration
        )
    
    # Similar methods for other budgets...

class BudgetManager:
    """Manages budget state transitions"""
    def __init__(self, initial: BudgetState):
        self._current = initial
        self._history = [initial]
        
    @property
    def current(self) -> BudgetState:
        return self._current
        
    def apply_depletion(self, 
                       effort: float = 0.0,
                       persistence: float = 0.0,
                       risk: float = 0.0,
                       exploration: float = 0.0) -> BudgetState:
        """Apply budget depletion (creates new state)"""
        new_state = BudgetState(
            effort=max(0.0, self._current.effort - effort),
            persistence=max(0.0, self._current.persistence - persistence),
            risk=max(0.0, self._current.risk - risk),
            exploration=max(0.0, self._current.exploration - exploration)
        )
        
        self._current = new_state
        self._history.append(new_state)
        
        return new_state
    
    def get_history(self) -> list[BudgetState]:
        """Audit trail of budget changes"""
        return self._history.copy()
```

**Key implementation rule:**
- Budgets are **immutable states**
- Every change creates new state (audit trail)
- No replenishment without explicit external reset

---

### 3. Evaluator (Governance Logic)

**Spec says:**
> The evaluator is a pure function: `decision = f(signals, budgets)`

**What you need to build:**

```python
# agentguard/evaluator/core.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class HaltReason(Enum):
    """Typed halt reasons (from spec)"""
    EXHAUSTION = "effort_budget_depleted"
    STAGNATION = "no_progress_across_window"
    PERSISTENCE_LIMIT = "retry_tolerance_exceeded"
    OVERRISK = "risk_threshold_crossed"
    EXPLORATION_DRIFT = "novelty_exceeds_bounds"
    EXTERNAL = "external_hard_stop"

@dataclass(frozen=True)
class GovernanceDecision:
    """Immutable governance decision"""
    allow: bool
    halt_reason: Optional[HaltReason]
    budget_snapshot: BudgetState
    signal_snapshot: dict
    step: int
    
    def to_audit_entry(self) -> dict:
        """Convert to audit log format"""
        return {
            "decision": "ALLOW" if self.allow else "HALT",
            "halt_reason": self.halt_reason.value if self.halt_reason else None,
            "budgets": {
                "effort": self.budget_snapshot.effort,
                "persistence": self.budget_snapshot.persistence,
                "risk": self.budget_snapshot.risk,
                "exploration": self.budget_snapshot.exploration,
            },
            "signals": self.signal_snapshot,
            "step": self.step
        }

class Evaluator:
    """Pure governance evaluator (deterministic)"""
    
    def __init__(self, 
                 exhaustion_threshold: float = 0.05,
                 stagnation_window: int = 10,
                 risk_threshold: float = 0.8,
                 exploration_threshold: float = 0.9):
        # Configuration (immutable after init)
        self.exhaustion_threshold = exhaustion_threshold
        self.stagnation_window = stagnation_window
        self.risk_threshold = risk_threshold
        self.exploration_threshold = exploration_threshold
        
        # State for stagnation detection
        self._progress_history = []
        
    def evaluate(self,
                signals: dict,
                budgets: BudgetState,
                step: int) -> GovernanceDecision:
        """
        Pure evaluation function.
        Same inputs → same output (deterministic).
        """
        
        # Priority order (from spec):
        # 1. EXPLORATION_DRIFT
        # 2. OVERRISK
        # 3. EXHAUSTION
        # 4. STAGNATION
        # 5. PERSISTENCE_LIMIT
        
        # 1. Check exploration drift
        if budgets.exploration > self.exploration_threshold:
            return GovernanceDecision(
                allow=False,
                halt_reason=HaltReason.EXPLORATION_DRIFT,
                budget_snapshot=budgets,
                signal_snapshot=signals,
                step=step
            )
        
        # 2. Check risk threshold
        if budgets.risk > self.risk_threshold:
            return GovernanceDecision(
                allow=False,
                halt_reason=HaltReason.OVERRISK,
                budget_snapshot=budgets,
                signal_snapshot=signals,
                step=step
            )
        
        # 3. Check exhaustion
        if budgets.effort <= self.exhaustion_threshold:
            return GovernanceDecision(
                allow=False,
                halt_reason=HaltReason.EXHAUSTION,
                budget_snapshot=budgets,
                signal_snapshot=signals,
                step=step
            )
        
        # 4. Check stagnation
        progress = signals.get('progress', 0.0)
        self._progress_history.append(progress)
        
        if len(self._progress_history) >= self.stagnation_window:
            recent_progress = self._progress_history[-self.stagnation_window:]
            if sum(recent_progress) == 0 and budgets.effort < 0.3:
                return GovernanceDecision(
                    allow=False,
                    halt_reason=HaltReason.STAGNATION,
                    budget_snapshot=budgets,
                    signal_snapshot=signals,
                    step=step
                )
        
        # 5. Check persistence limit
        if budgets.persistence <= 0.0:
            return GovernanceDecision(
                allow=False,
                halt_reason=HaltReason.PERSISTENCE_LIMIT,
                budget_snapshot=budgets,
                signal_snapshot=signals,
                step=step
            )
        
        # All checks passed
        return GovernanceDecision(
            allow=True,
            halt_reason=None,
            budget_snapshot=budgets,
            signal_snapshot=signals,
            step=step
        )
```

**Key implementation rule:**
- Evaluator is **pure function** (no side effects)
- Deterministic (same inputs → same decision)
- Priority ordering of checks is explicit and documented

---

### 4. Enforcer (Physical Blocking)

**Spec says:**
> The enforcement layer physically enacts the evaluator's decision. The agent cannot execute without approval.

**What you need to build:**

```python
# agentguard/enforcement/base.py
from abc import ABC, abstractmethod
from typing import Any, Callable

class Enforcer(ABC):
    """Base enforcer interface"""
    
    @abstractmethod
    def intercept(self, action: dict, evaluator: Evaluator) -> dict:
        """
        Intercept action attempt.
        Returns result if allowed, raises EnforcementBlock if not.
        """
        pass

class EnforcementBlock(Exception):
    """Raised when action is blocked"""
    def __init__(self, reason: HaltReason, decision: GovernanceDecision):
        self.reason = reason
        self.decision = decision
        super().__init__(f"Action blocked: {reason.value}")

# Option 1: In-Process Enforcer (weakest, but easiest to start)
class InProcessEnforcer(Enforcer):
    """
    Wraps tool functions to enforce governance.
    NOTE: Agent can bypass by calling tools directly.
    """
    def __init__(self, tools: dict[str, Callable]):
        self.tools = tools
        self.governed_tools = {}
        
        # Wrap each tool
        for name, func in tools.items():
            self.governed_tools[name] = self._wrap_tool(name, func)
    
    def _wrap_tool(self, name: str, func: Callable) -> Callable:
        """Wrap tool with governance check"""
        def governed_func(*args, **kwargs):
            # Check with evaluator
            decision = self.evaluator.evaluate(...)
            
            if not decision.allow:
                raise EnforcementBlock(decision.halt_reason, decision)
            
            # Execute if allowed
            return func(*args, **kwargs)
        
        return governed_func

# Option 2: HTTP Proxy Enforcer (stronger, production-grade)
class HTTPProxyEnforcer(Enforcer):
    """
    Runs as HTTP proxy between agent and tools.
    Agent must route ALL tool calls through proxy.
    """
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = self._create_app()
        
    def _create_app(self):
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/tool/<tool_name>', methods=['POST'])
        def execute_tool(tool_name):
            # Extract action details
            action = {
                "tool": tool_name,
                "params": request.json,
                "timestamp": time.time()
            }
            
            # Get current signals and budgets
            signals = self._extract_signals(action)
            budgets = self.budget_manager.current
            
            # Evaluate
            decision = self.evaluator.evaluate(signals, budgets, self.step)
            
            # Log decision
            self.audit_logger.log(decision)
            
            # Enforce
            if not decision.allow:
                return jsonify({
                    "status": "blocked",
                    "reason": decision.halt_reason.value,
                    "budgets": decision.budget_snapshot.__dict__
                }), 403
            
            # Execute tool
            result = self._execute_tool(tool_name, request.json)
            
            # Update budgets based on execution
            self._update_budgets(action, result)
            
            self.step += 1
            
            return jsonify(result)
        
        return app
    
    def start(self):
        """Start enforcement proxy"""
        self.app.run(port=self.port)

# Option 3: Sidecar Enforcer (strongest, cloud-native)
class SidecarEnforcer(Enforcer):
    """
    Runs as sidecar container.
    Intercepts network calls at iptables/envoy level.
    Agent CANNOT bypass (enforced by infrastructure).
    """
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.iptables_rules = self._generate_iptables()
        
    def deploy(self):
        """Deploy sidecar with iptables rules"""
        # This would integrate with K8s/Docker
        # to enforce network-level blocking
        pass
```

**Key implementation rule:**
- Start with **InProcessEnforcer** (proves concept)
- Move to **HTTPProxyEnforcer** (production-ready)
- Eventually **SidecarEnforcer** (infrastructure-grade)

---

### 5. Audit Trail (Reconstructability)

**Spec says:**
> Every harness must emit an execution trace. Append-only, ordered, immutable, machine-readable.

**What you need to build:**

```python
# agentguard/audit/logger.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json
import hashlib

@dataclass
class AuditEntry:
    """Single audit log entry"""
    execution_id: str
    timestamp: datetime
    step: int
    agent_id: str
    
    # Action details
    action: dict
    
    # Governance state
    signals: dict
    budgets: dict
    
    # Decision
    decision: str  # "ALLOW" or "HALT"
    halt_reason: Optional[str]
    
    # Linkage (for tamper detection)
    previous_hash: Optional[str]
    entry_hash: str
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(asdict(self), default=str)
    
    @staticmethod
    def compute_hash(entry_dict: dict) -> str:
        """Compute hash for tamper detection"""
        canonical = json.dumps(entry_dict, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

class AuditLogger:
    """Immutable audit trail"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.last_hash = None
        
    def log(self, decision: GovernanceDecision, action: dict, agent_id: str):
        """Append entry to audit trail"""
        
        entry_data = {
            "execution_id": self.storage.execution_id,
            "timestamp": datetime.utcnow(),
            "step": decision.step,
            "agent_id": agent_id,
            "action": action,
            "signals": decision.signal_snapshot,
            "budgets": {
                "effort": decision.budget_snapshot.effort,
                "persistence": decision.budget_snapshot.persistence,
                "risk": decision.budget_snapshot.risk,
                "exploration": decision.budget_snapshot.exploration,
            },
            "decision": "ALLOW" if decision.allow else "HALT",
            "halt_reason": decision.halt_reason.value if decision.halt_reason else None,
            "previous_hash": self.last_hash,
            "entry_hash": ""  # Computed below
        }
        
        # Compute hash (links to previous entry)
        entry_data["entry_hash"] = AuditEntry.compute_hash(entry_data)
        
        entry = AuditEntry(**entry_data)
        
        # Store
        self.storage.append(entry)
        
        # Update chain
        self.last_hash = entry.entry_hash
        
        return entry

# Storage backends
class PostgreSQLAuditStorage:
    """Store audit trail in PostgreSQL"""
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self.execution_id = str(uuid.uuid4())
        
    def append(self, entry: AuditEntry):
        """Insert entry (append-only)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail 
            (execution_id, timestamp, step, agent_id, action, 
             signals, budgets, decision, halt_reason, 
             previous_hash, entry_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            entry.execution_id,
            entry.timestamp,
            entry.step,
            entry.agent_id,
            json.dumps(entry.action),
            json.dumps(entry.signals),
            json.dumps(entry.budgets),
            entry.decision,
            entry.halt_reason,
            entry.previous_hash,
            entry.entry_hash
        ))
        self.conn.commit()
    
    def verify_chain(self) -> bool:
        """Verify audit trail hasn't been tampered with"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entry_hash, previous_hash 
            FROM audit_trail 
            WHERE execution_id = %s 
            ORDER BY step
        """, (self.execution_id,))
        
        entries = cursor.fetchall()
        
        for i in range(1, len(entries)):
            current_entry = entries[i]
            previous_entry = entries[i-1]
            
            if current_entry[1] != previous_entry[0]:  # previous_hash mismatch
                return False
        
        return True
```

**Key implementation rule:**
- Audit trail is **append-only** (no updates/deletes)
- Each entry links to previous (blockchain-style chaining)
- Tamper detection via hash verification

---

## The Minimal Complete System (What to Build First)

To satisfy your spec's **5 litmus test criteria**, you need:

### Week 1-2: Core Components
```
✅ 1. Signal extraction system
✅ 2. Budget management
✅ 3. Pure evaluator
✅ 4. In-process enforcer (weakest, but proves concept)
✅ 5. Audit logger (PostgreSQL)
```

**Test:** Can an agent be prevented from exceeding limits?

### Week 3-4: Enforcement Upgrade
```
✅ 6. HTTP proxy enforcer
✅ 7. Integration with LangChain/AutoGen
```

**Test:** Can agent bypass governance? (Answer must be NO)

### Week 5-6: Multi-Agent
```
✅ 8. Shared budget pools
✅ 9. Cascade detection
```

**Test:** Can multi-agent system be governed?
