#!/usr/bin/env python3
"""
Tests for the policy engine module.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from governance.policy_engine import (
    PolicyEngine, Policy, PolicyContext, PolicyDecision, PolicyResult, PolicyVerdict,
    MaxStepsPolicy, MaxTokensPolicy, AllowedToolsPolicy, RateLimitPolicy, TimeoutPolicy
)


class TestPolicyContext:
    """Tests for PolicyContext."""
    
    def test_default_values(self):
        """PolicyContext should have sensible defaults."""
        ctx = PolicyContext()
        assert ctx.step == 0
        assert ctx.tokens_used == 0
        assert ctx.tool_name is None
        assert ctx.effort_budget == 1.0
    
    def test_custom_values(self):
        """PolicyContext should accept custom values."""
        ctx = PolicyContext(
            step=50,
            tool_name="search",
            tokens_used=5000
        )
        assert ctx.step == 50
        assert ctx.tool_name == "search"
        assert ctx.tokens_used == 5000


class TestMaxStepsPolicy:
    """Tests for MaxStepsPolicy."""
    
    def test_allow_under_limit(self):
        """Should allow when under the step limit."""
        policy = MaxStepsPolicy(max_steps=100)
        ctx = PolicyContext(step=50)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_warn_near_limit(self):
        """Should warn when approaching limit (90%)."""
        policy = MaxStepsPolicy(max_steps=100)
        ctx = PolicyContext(step=95)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.WARN
    
    def test_deny_at_limit(self):
        """Should deny when at or over limit."""
        policy = MaxStepsPolicy(max_steps=100)
        ctx = PolicyContext(step=100)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.DENY
        assert "100" in result.reason


class TestMaxTokensPolicy:
    """Tests for MaxTokensPolicy."""
    
    def test_allow_under_limit(self):
        """Should allow when under token limit."""
        policy = MaxTokensPolicy(max_tokens=10000)
        ctx = PolicyContext(tokens_used=5000)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_deny_at_limit(self):
        """Should deny when at or over limit."""
        policy = MaxTokensPolicy(max_tokens=10000)
        ctx = PolicyContext(tokens_used=10000)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.DENY


class TestAllowedToolsPolicy:
    """Tests for AllowedToolsPolicy."""
    
    def test_no_tool(self):
        """Should allow when no tool is specified."""
        policy = AllowedToolsPolicy(allowed={"search"})
        ctx = PolicyContext()
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_whitelist_allowed(self):
        """Should allow whitelisted tool."""
        policy = AllowedToolsPolicy(allowed={"search", "calculator"})
        ctx = PolicyContext(tool_name="search")
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_whitelist_denied(self):
        """Should deny non-whitelisted tool."""
        policy = AllowedToolsPolicy(allowed={"search"})
        ctx = PolicyContext(tool_name="delete_file")
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.DENY
    
    def test_blacklist_denied(self):
        """Should deny blacklisted tool."""
        policy = AllowedToolsPolicy(blocked={"delete_file", "format_disk"})
        ctx = PolicyContext(tool_name="delete_file")
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.DENY


class TestTimeoutPolicy:
    """Tests for TimeoutPolicy."""
    
    def test_allow_under_timeout(self):
        """Should allow when under timeout."""
        policy = TimeoutPolicy(max_seconds=300)
        ctx = PolicyContext(elapsed_seconds=100)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_deny_at_timeout(self):
        """Should deny when at or over timeout."""
        policy = TimeoutPolicy(max_seconds=300)
        ctx = PolicyContext(elapsed_seconds=300)
        result = policy.evaluate(ctx)
        assert result.verdict == PolicyVerdict.DENY


class TestPolicyEngine:
    """Tests for PolicyEngine."""
    
    def test_empty_engine_allows(self):
        """Empty engine should allow everything."""
        engine = PolicyEngine()
        ctx = PolicyContext()
        result = engine.evaluate(ctx)
        assert not result.blocked
    
    def test_single_policy_deny(self):
        """Engine should block when any policy denies."""
        engine = PolicyEngine()
        engine.add_policy(MaxStepsPolicy(max_steps=10))
        
        ctx = PolicyContext(step=20)
        result = engine.evaluate(ctx)
        
        assert result.blocked
        assert result.blocking_policy == "max_steps"
    
    def test_multiple_policies(self):
        """Engine should evaluate all policies."""
        engine = PolicyEngine()
        engine.add_policy(MaxStepsPolicy(max_steps=100))
        engine.add_policy(MaxTokensPolicy(max_tokens=10000))
        
        ctx = PolicyContext(step=50, tokens_used=5000)
        result = engine.evaluate(ctx)
        
        assert not result.blocked
        assert len(result.decisions) == 2
    
    def test_first_deny_wins(self):
        """First denying policy should be the blocking one."""
        engine = PolicyEngine()
        engine.add_policy(MaxStepsPolicy(max_steps=10))
        engine.add_policy(MaxTokensPolicy(max_tokens=100))
        
        ctx = PolicyContext(step=20, tokens_used=200)  # Both would deny
        result = engine.evaluate(ctx)
        
        assert result.blocked
        assert result.blocking_policy == "max_steps"  # First one
    
    def test_warnings_collected(self):
        """Warnings should be collected but not block."""
        engine = PolicyEngine()
        engine.add_policy(MaxStepsPolicy(max_steps=100))
        
        ctx = PolicyContext(step=95)  # In warning zone
        result = engine.evaluate(ctx)
        
        assert not result.blocked
        assert len(result.warnings) == 1
    
    def test_chaining(self):
        """add_policy should return self for chaining."""
        engine = PolicyEngine()
        result = engine.add_policy(MaxStepsPolicy(100)).add_policy(MaxTokensPolicy(10000))
        
        assert result is engine
        assert len(engine.policies) == 2


class TestRateLimitPolicy:
    """Tests for RateLimitPolicy."""
    
    def test_allow_under_limit(self):
        """Should allow when under rate limit."""
        policy = RateLimitPolicy(max_actions_per_minute=10)
        ctx = PolicyContext()
        
        for _ in range(5):
            result = policy.evaluate(ctx)
        
        assert result.verdict == PolicyVerdict.ALLOW
    
    def test_deny_at_limit(self):
        """Should deny when rate limit exceeded."""
        policy = RateLimitPolicy(max_actions_per_minute=5)
        ctx = PolicyContext()
        
        for _ in range(5):
            policy.evaluate(ctx)
        
        result = policy.evaluate(ctx)  # 6th call
        assert result.verdict == PolicyVerdict.DENY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
