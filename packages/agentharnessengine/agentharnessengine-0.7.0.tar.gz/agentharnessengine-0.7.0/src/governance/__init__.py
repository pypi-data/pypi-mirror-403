# emocore/__init__.py
"""
EmoCore - Runtime Governance for Autonomous Agents

Public API:
    from governance import EmoCoreAgent, step, Signals
    from governance.profiles import PROFILES, ProfileType

Usage:
    agent = EmoCoreAgent()
    result = step(agent, Signals(reward=0.5, novelty=0.1, urgency=0.2))
"""

from governance.agent import EmoCoreAgent
from governance.interface import step, observe, Signals
from governance.observation import Observation
from governance.adapters import LLMLoopAdapter, ToolCallingAgentAdapter
from governance.guarantees import StepResult, GuaranteeEnforcer
from governance.failures import FailureType
from governance.modes import Mode
from governance.behavior import BehaviorBudget
from governance.state import ControlState
from governance.profiles import Profile, PROFILES, ProfileType
from governance.metrics import GovernanceMetrics, MetricsCollector
from governance.audit import AuditLogger, AuditEntry
from governance.enforcement import InProcessEnforcer, EnforcementBlocked
from governance.policy_engine import (
    PolicyEngine, Policy, PolicyContext, PolicyDecision, PolicyResult, PolicyVerdict,
    MaxStepsPolicy, MaxTokensPolicy, AllowedToolsPolicy, RateLimitPolicy, TimeoutPolicy
)
from governance.guardrails import (
    GuardrailStack, Guardrail, GuardrailResult, GuardrailSeverity,
    PromptInjectionDetector, PIIDetector, ToolAuthorizationGuard,
    ContentLengthGuard, CodeExecutionGuard
)
from governance.coordination import (
    SystemGovernor, SharedBudgetPool, CascadeDetector, AgentRegistry,
    AgentState, SystemHealthReport, SystemStatus
)

# Backward compatibility aliases
PressureState = ControlState

__all__ = [
    # Main API
    "EmoCoreAgent",
    "step",
    "observe",
    "Signals",
    "Observation",
    "StepResult",
    # Adapters
    "LLMLoopAdapter",
    "ToolCallingAgentAdapter",
    # Types
    "FailureType",
    "Mode",
    "BehaviorBudget",
    "ControlState",
    "PressureState",  # Alias
    # Profiles
    "Profile",
    "PROFILES",
    "ProfileType",
    # Guarantees
    "GuaranteeEnforcer",
    # Observability
    "GovernanceMetrics",
    "MetricsCollector",
    # Audit & Enforcement
    "AuditLogger",
    "AuditEntry",
    "InProcessEnforcer",
    "EnforcementBlocked",
    # Policy Engine
    "PolicyEngine",
    "Policy",
    "PolicyContext",
    "PolicyDecision",
    "PolicyResult",
    "PolicyVerdict",
    "MaxStepsPolicy",
    "MaxTokensPolicy",
    "AllowedToolsPolicy",
    "RateLimitPolicy",
    "TimeoutPolicy",
    # Guardrails
    "GuardrailStack",
    "Guardrail",
    "GuardrailResult",
    "GuardrailSeverity",
    "PromptInjectionDetector",
    "PIIDetector",
    "ToolAuthorizationGuard",
    "ContentLengthGuard",
    "CodeExecutionGuard",
    # Multi-Agent Coordination
    "SystemGovernor",
    "SharedBudgetPool",
    "CascadeDetector",
    "AgentRegistry",
    "AgentState",
    "SystemHealthReport",
    "SystemStatus",
]

__version__ = "0.7.0"
