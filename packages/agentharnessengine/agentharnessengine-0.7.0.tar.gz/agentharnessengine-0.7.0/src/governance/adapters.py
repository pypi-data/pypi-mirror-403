# emocore/adapters.py
"""
Integration Surface: Reusable adapters for typical agent loops.
These wrappers simplify the 'observe()' pattern by handling timing and
Observation construction automatically.
"""

import time
from typing import Optional, Any, Callable
from contextlib import contextmanager

from governance.observation import Observation
from governance.interface import observe, StepResult
from governance.agent import EmoCoreAgent


class LLMLoopAdapter:
    """
    Adapter for standard generative LLM loops.
    
    Automatically tracks time and constructs Observations from
    high-level execution results.
    """
    
    def __init__(self, agent: EmoCoreAgent, token_limit: int = 100000):
        self.agent = agent
        self.token_limit = token_limit
        self.last_step_start = 0.0
        
    def start_step(self):
        """Mark the start of an LLM generation step."""
        self.last_step_start = time.monotonic()
        
    def end_step(
        self, 
        action: str, 
        result: str, 
        env_delta: float = 0.0, 
        agent_delta: float = 0.1,
        tokens_used: int = 0,
        error: Optional[str] = None,
        extractor: Any = None,
        validator: Any = None
    ) -> StepResult:
        """
        Produce an EmoCore governance decision for the completed step.
        """
        elapsed = time.monotonic() - self.last_step_start
        
        obs = Observation(
            action=action,
            result=result,
            env_state_delta=env_delta,
            agent_state_delta=agent_delta,
            elapsed_time=elapsed,
            tokens_used=tokens_used,
            error=error
        )
        
        # If no extractor provided, try to use LLMAgentExtractor with our token limit
        if extractor is None and not hasattr(self.agent, '_extractor'):
             from governance.extractor import LLMAgentExtractor
             self.agent._extractor = LLMAgentExtractor(token_limit=self.token_limit)
        
        return observe(self.agent, obs, extractor=extractor, validator=validator)


class ToolCallingAgentAdapter:
    """
    Adapter for agents that execute tools/functions.
    
    Provides a context manager for auditing tool executions.
    """
    
    def __init__(self, agent: EmoCoreAgent):
        self.agent = agent
        
    @contextmanager
    def monitor(self, tool_name: str):
        """
        Audit a tool execution.
        
        Usage:
            with adapter.monitor("search") as result:
                res = do_search()
                result.success(env_delta=0.8)
        """
        start_time = time.monotonic()
        state = {"status": "failure", "env_delta": 0.0, "agent_delta": 0.1, "error": None}
        
        class Auditor:
            def success(self, env_delta: float = 0.1, agent_delta: float = 0.1):
                state["status"] = "success"
                state["env_delta"] = env_delta
                state["agent_delta"] = agent_delta
            
            def error(self, msg: str):
                state["status"] = "error"
                state["error"] = msg
        
        auditor = Auditor()
        try:
            yield auditor
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            raise
        finally:
            elapsed = time.monotonic() - start_time
            obs = Observation(
                action=tool_name,
                result=state["status"],
                env_state_delta=state["env_delta"],
                agent_state_delta=state["agent_delta"],
                elapsed_time=elapsed,
                error=state["error"]
            )
            # We store the result on the auditor for optional retrieval
            
            # If no extractor exists, default to ToolAgentExtractor
            if not hasattr(self.agent, '_extractor'):
                from governance.extractor import ToolAgentExtractor
                self.agent._extractor = ToolAgentExtractor()
                
            auditor.governance_result = observe(self.agent, obs)
