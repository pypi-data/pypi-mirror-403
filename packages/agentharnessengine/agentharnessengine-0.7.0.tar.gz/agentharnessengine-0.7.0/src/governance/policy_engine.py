# src/governance/policy_engine.py
"""
Policy Engine: Pluggable policy evaluation system for governance.

This module provides:
- Policy: Base class for custom policies
- PolicyContext: Input context for policy evaluation
- PolicyDecision: Single policy verdict
- PolicyEngine: Aggregates multiple policies

Usage:
    from governance.policy_engine import PolicyEngine, MaxStepsPolicy
    
    engine = PolicyEngine()
    engine.add_policy(MaxStepsPolicy(max_steps=100))
    engine.add_policy(AllowedToolsPolicy(allowed=["search", "calculator"]))
    
    result = engine.evaluate(PolicyContext(
        step=45,
        tool_name="search",
        tokens_used=1500
    ))
    
    if result.blocked:
        print(f"Blocked by: {result.blocking_policy}")
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timezone


class PolicyVerdict(Enum):
    """Result of a single policy evaluation."""
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


@dataclass
class PolicyContext:
    """
    Context provided to policies for evaluation.
    
    This contains all information a policy might need to make a decision.
    Not all fields are required - policies should handle missing data gracefully.
    """
    # Execution state
    step: int = 0
    tokens_used: int = 0
    elapsed_seconds: float = 0.0
    
    # Current action
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    
    # Content (for guardrails)
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    
    # Agent state
    effort_budget: float = 1.0
    risk_budget: float = 0.0
    halted: bool = False
    
    # Metadata
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class PolicyDecision:
    """
    Decision from a single policy.
    """
    policy_name: str
    verdict: PolicyVerdict
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PolicyResult:
    """
    Aggregated result from all policies.
    """
    decisions: List[PolicyDecision]
    blocked: bool = False
    blocking_policy: Optional[str] = None
    blocking_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocked": self.blocked,
            "blocking_policy": self.blocking_policy,
            "blocking_reason": self.blocking_reason,
            "warnings": self.warnings,
            "decisions": [
                {"policy": d.policy_name, "verdict": d.verdict.value, "reason": d.reason}
                for d in self.decisions
            ]
        }


class Policy(ABC):
    """
    Base class for governance policies.
    
    Implement this to create custom policies that can be plugged
    into the PolicyEngine.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this policy."""
        pass
    
    @abstractmethod
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """
        Evaluate the policy against the given context.
        
        Args:
            context: The current execution context
            
        Returns:
            PolicyDecision with verdict and reason
        """
        pass


class PolicyEngine:
    """
    Evaluates multiple policies and aggregates their decisions.
    
    Policies are evaluated in order. If any policy returns DENY,
    the overall result is blocked. WARN verdicts are collected
    but don't block execution.
    """
    
    def __init__(self, fail_closed: bool = True):
        """
        Args:
            fail_closed: If True, any policy error results in DENY
        """
        self._policies: List[Policy] = []
        self._fail_closed = fail_closed
    
    def add_policy(self, policy: Policy) -> "PolicyEngine":
        """Add a policy to the engine. Returns self for chaining."""
        self._policies.append(policy)
        return self
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name. Returns True if found."""
        for i, p in enumerate(self._policies):
            if p.name == policy_name:
                self._policies.pop(i)
                return True
        return False
    
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """
        Evaluate all policies against the context.
        
        Returns:
            PolicyResult with aggregated decisions
        """
        decisions: List[PolicyDecision] = []
        warnings: List[str] = []
        blocked = False
        blocking_policy = None
        blocking_reason = None
        
        for policy in self._policies:
            try:
                decision = policy.evaluate(context)
                decisions.append(decision)
                
                if decision.verdict == PolicyVerdict.DENY and not blocked:
                    blocked = True
                    blocking_policy = decision.policy_name
                    blocking_reason = decision.reason
                elif decision.verdict == PolicyVerdict.WARN:
                    warnings.append(f"{decision.policy_name}: {decision.reason}")
                    
            except Exception as e:
                if self._fail_closed:
                    blocked = True
                    blocking_policy = policy.name
                    blocking_reason = f"Policy error: {str(e)}"
                    decisions.append(PolicyDecision(
                        policy_name=policy.name,
                        verdict=PolicyVerdict.DENY,
                        reason=f"Policy error: {str(e)}"
                    ))
                else:
                    warnings.append(f"{policy.name}: Error - {str(e)}")
        
        return PolicyResult(
            decisions=decisions,
            blocked=blocked,
            blocking_policy=blocking_policy,
            blocking_reason=blocking_reason,
            warnings=warnings,
        )
    
    @property
    def policies(self) -> List[str]:
        """List of registered policy names."""
        return [p.name for p in self._policies]


# ============================================================================
# Built-in Policies
# ============================================================================

class MaxStepsPolicy(Policy):
    """Enforce a maximum number of execution steps."""
    
    def __init__(self, max_steps: int = 100):
        self._max_steps = max_steps
    
    @property
    def name(self) -> str:
        return "max_steps"
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.step >= self._max_steps:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Maximum steps ({self._max_steps}) exceeded"
            )
        elif context.step >= self._max_steps * 0.9:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.WARN,
                reason=f"Approaching step limit ({context.step}/{self._max_steps})"
            )
        return PolicyDecision(
            policy_name=self.name,
            verdict=PolicyVerdict.ALLOW
        )


class MaxTokensPolicy(Policy):
    """Enforce a maximum token consumption limit."""
    
    def __init__(self, max_tokens: int = 100000):
        self._max_tokens = max_tokens
    
    @property
    def name(self) -> str:
        return "max_tokens"
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.tokens_used >= self._max_tokens:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Maximum tokens ({self._max_tokens}) exceeded"
            )
        elif context.tokens_used >= self._max_tokens * 0.9:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.WARN,
                reason=f"Approaching token limit ({context.tokens_used}/{self._max_tokens})"
            )
        return PolicyDecision(
            policy_name=self.name,
            verdict=PolicyVerdict.ALLOW
        )


class AllowedToolsPolicy(Policy):
    """Restrict which tools can be used."""
    
    def __init__(
        self,
        allowed: Optional[Set[str]] = None,
        blocked: Optional[Set[str]] = None
    ):
        """
        Args:
            allowed: If set, only these tools are allowed (whitelist)
            blocked: If set, these tools are blocked (blacklist)
        """
        self._allowed = set(allowed) if allowed else None
        self._blocked = set(blocked) if blocked else set()
    
    @property
    def name(self) -> str:
        return "allowed_tools"
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.tool_name is None:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.ALLOW
            )
        
        tool = context.tool_name.lower()
        
        # Check blacklist
        if tool in self._blocked:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Tool '{context.tool_name}' is blocked"
            )
        
        # Check whitelist
        if self._allowed is not None and tool not in self._allowed:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Tool '{context.tool_name}' is not in allowed list"
            )
        
        return PolicyDecision(
            policy_name=self.name,
            verdict=PolicyVerdict.ALLOW
        )


class RateLimitPolicy(Policy):
    """Enforce rate limits on actions."""
    
    def __init__(self, max_actions_per_minute: int = 60):
        self._max_per_minute = max_actions_per_minute
        self._action_times: List[float] = []
    
    @property
    def name(self) -> str:
        return "rate_limit"
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        import time
        now = time.time()
        
        # Clean old entries (older than 60 seconds)
        self._action_times = [t for t in self._action_times if now - t < 60]
        
        if len(self._action_times) >= self._max_per_minute:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Rate limit exceeded ({self._max_per_minute}/min)"
            )
        
        self._action_times.append(now)
        
        return PolicyDecision(
            policy_name=self.name,
            verdict=PolicyVerdict.ALLOW
        )


class TimeoutPolicy(Policy):
    """Enforce a maximum execution time."""
    
    def __init__(self, max_seconds: float = 300.0):
        self._max_seconds = max_seconds
    
    @property
    def name(self) -> str:
        return "timeout"
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.elapsed_seconds >= self._max_seconds:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.DENY,
                reason=f"Execution timeout ({self._max_seconds}s) exceeded"
            )
        elif context.elapsed_seconds >= self._max_seconds * 0.9:
            return PolicyDecision(
                policy_name=self.name,
                verdict=PolicyVerdict.WARN,
                reason=f"Approaching timeout ({context.elapsed_seconds:.1f}/{self._max_seconds}s)"
            )
        return PolicyDecision(
            policy_name=self.name,
            verdict=PolicyVerdict.ALLOW
        )
