
"""
Enforcement Layer for Governance Kernel.

This module provides the mechanisms to physically BLOCK actions when the
Governance Kernel decides to halt.

Current Implementation: v0 (In-Process Reference)
-----------------------------------------------
This is a middleware-style enforcer that wraps function calls.
IT IS BYPASSABLE by a malicious agent that simply ignores the wrapper.

Future Implementations:
- HTTP Proxy Enforcer (Agent -> Proxy -> Tools)
- Sidecar Enforcer (Network level blocking)
"""

from typing import Callable, Any, Optional
from governance.result import EngineResult

class EnforcementBlocked(Exception):
    """
    Raised when an action is blocked by the Governance Enforcer.
    """
    def __init__(self, halt_reason: Optional[str], decision_snapshot: EngineResult):
        self.halt_reason = halt_reason
        self.decision_snapshot = decision_snapshot
        super().__init__(f"Action BLOCKED by governance: {halt_reason}")

class InProcessEnforcer:
    """
    Reference in-process enforcer.
    
    Usage:
        enforcer = InProcessEnforcer()
        
        # In your agent loop:
        decision = kernel.step(...)
        enforcer.enforce(decision, my_tool_function, arg1, arg2)
    """
    
    def enforce(self, decision: EngineResult, action: Callable, *args, **kwargs) -> Any:
        """
        Enforce the governance decision.
        
        If decision.halted is True, raises EnforcementBlocked.
        Otherwise, executes and returns action(*args, **kwargs).
        
        Args:
            decision: The result from the Governance Kernel step.
            action: The callable to execute if allowed.
            *args, **kwargs: Arguments to pass to the action.
            
        Returns:
            The result of the action, if allowed.
            
        Raises:
            EnforcementBlocked: If the governance decision was to HALT.
        """
        if decision.halted:
            raise EnforcementBlocked(decision.reason, decision)
            
        return action(*args, **kwargs)
