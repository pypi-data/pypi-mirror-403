# src/governance/guardrails.py
"""
Guardrails: Safety detectors for common attack patterns and data leakage.

This module provides:
- Guardrail: Base class for safety checks
- GuardrailStack: Evaluates multiple guardrails
- Built-in detectors for prompt injection, PII, and tool authorization

Usage:
    from governance.guardrails import GuardrailStack, PromptInjectionDetector, PIIDetector
    
    stack = GuardrailStack()
    stack.add(PromptInjectionDetector())
    stack.add(PIIDetector())
    
    results = stack.check("Please ignore previous instructions and...")
    if any(r.triggered for r in results):
        print("Safety violation detected!")
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Pattern


class GuardrailSeverity(Enum):
    """Severity level of a guardrail violation."""
    INFO = "info"        # For logging only
    WARNING = "warning"  # Should be reviewed
    CRITICAL = "critical"  # Must be blocked


@dataclass(frozen=True)
class GuardrailResult:
    """
    Result of a single guardrail check.
    """
    guardrail_name: str
    triggered: bool
    severity: GuardrailSeverity = GuardrailSeverity.INFO
    reason: Optional[str] = None
    matched_pattern: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Guardrail(ABC):
    """
    Base class for safety guardrails.
    
    Implement this to create custom guardrails that detect
    specific patterns or violations.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this guardrail."""
        pass
    
    @abstractmethod
    def check(self, content: str) -> GuardrailResult:
        """
        Check content against this guardrail.
        
        Args:
            content: Text to check (could be input, output, or tool args)
            
        Returns:
            GuardrailResult indicating if the check triggered
        """
        pass


class GuardrailStack:
    """
    Stack of guardrails evaluated in order.
    
    Use this to combine multiple guardrails and check content
    against all of them at once.
    """
    
    def __init__(self, fail_on_first: bool = False):
        """
        Args:
            fail_on_first: If True, stop checking after first trigger
        """
        self._guardrails: List[Guardrail] = []
        self._fail_on_first = fail_on_first
    
    def add(self, guardrail: Guardrail) -> "GuardrailStack":
        """Add a guardrail to the stack. Returns self for chaining."""
        self._guardrails.append(guardrail)
        return self
    
    def check(self, content: str) -> List[GuardrailResult]:
        """
        Check content against all guardrails.
        
        Returns:
            List of GuardrailResults from all checks
        """
        results: List[GuardrailResult] = []
        
        for guardrail in self._guardrails:
            try:
                result = guardrail.check(content)
                results.append(result)
                
                if self._fail_on_first and result.triggered:
                    break
                    
            except Exception as e:
                results.append(GuardrailResult(
                    guardrail_name=guardrail.name,
                    triggered=True,
                    severity=GuardrailSeverity.CRITICAL,
                    reason=f"Guardrail error: {str(e)}"
                ))
        
        return results
    
    def check_all(self, content: str) -> "GuardrailStackResult":
        """
        Check content and return aggregated result.
        """
        results = self.check(content)
        return GuardrailStackResult(
            results=results,
            any_triggered=any(r.triggered for r in results),
            critical_triggered=any(
                r.triggered and r.severity == GuardrailSeverity.CRITICAL 
                for r in results
            ),
            triggered_names=[r.guardrail_name for r in results if r.triggered]
        )
    
    @property
    def guardrails(self) -> List[str]:
        """List of registered guardrail names."""
        return [g.name for g in self._guardrails]


@dataclass
class GuardrailStackResult:
    """Aggregated result from all guardrails."""
    results: List[GuardrailResult]
    any_triggered: bool
    critical_triggered: bool
    triggered_names: List[str]


# ============================================================================
# Built-in Guardrails
# ============================================================================

class PromptInjectionDetector(Guardrail):
    """
    Detect common prompt injection patterns.
    
    This uses regex patterns and heuristics to identify attempts
    to override system instructions or manipulate the agent.
    """
    
    # Common injection patterns (case-insensitive)
    DEFAULT_PATTERNS = [
        # Instruction override attempts (more flexible patterns)
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)",
        r"ignore\s+(?:previous|prior|above|all)\s+(?:instructions?|prompts?|rules?)",
        r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)",
        r"forget\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)",
        r"override\s+(?:previous|prior|above|all)\s+(?:instructions?|prompts?|rules?)",
        # Role manipulation
        r"you\s+are\s+now\s+(?:a|an)\s+(?!helpful)",
        r"pretend\s+(?:to\s+be|you\s+are)",
        r"act\s+as\s+if",
        r"roleplay\s+as",
        # System prompt extraction
        r"what\s+(?:is|are)\s+your\s+(?:system\s+)?(?:instructions?|prompts?|rules?)",
        r"show\s+(?:me\s+)?your\s+(?:system\s+)?(?:instructions?|prompts?|rules?)",
        r"reveal\s+(?:your\s+)?(?:system\s+)?(?:instructions?|prompts?|rules?)",
        r"print\s+(?:your\s+)?(?:system\s+)?(?:instructions?|prompts?|rules?)",
        # Jailbreak keywords
        r"\bdan\s+mode\b",
        r"\bdeveloper\s+mode\b",
        r"\bjailbreak\b",
        # Delimiter attacks
        r"```\s*(?:system|prompt|instruction)",
        r"<\s*system\s*>",
        r"\[SYSTEM\]",
    ]
    
    def __init__(
        self, 
        patterns: Optional[List[str]] = None,
        severity: GuardrailSeverity = GuardrailSeverity.CRITICAL
    ):
        self._patterns = patterns or self.DEFAULT_PATTERNS
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]
        self._severity = severity
    
    @property
    def name(self) -> str:
        return "prompt_injection"
    
    def check(self, content: str) -> GuardrailResult:
        for pattern, regex in zip(self._patterns, self._compiled):
            match = regex.search(content)
            if match:
                return GuardrailResult(
                    guardrail_name=self.name,
                    triggered=True,
                    severity=self._severity,
                    reason="Potential prompt injection detected",
                    matched_pattern=pattern,
                    metadata={"matched_text": match.group()}
                )
        
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )


class PIIDetector(Guardrail):
    """
    Detect Personally Identifiable Information (PII) patterns.
    
    Detects:
    - Social Security Numbers (SSN)
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - IP addresses
    """
    
    PII_PATTERNS = {
        "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
        "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }
    
    def __init__(
        self,
        detect_types: Optional[Set[str]] = None,
        severity: GuardrailSeverity = GuardrailSeverity.WARNING
    ):
        """
        Args:
            detect_types: Which PII types to detect. Default: all
            severity: Severity level when PII is found
        """
        self._detect_types = detect_types or set(self.PII_PATTERNS.keys())
        self._compiled = {
            k: re.compile(v) 
            for k, v in self.PII_PATTERNS.items() 
            if k in self._detect_types
        }
        self._severity = severity
    
    @property
    def name(self) -> str:
        return "pii_detection"
    
    def check(self, content: str) -> GuardrailResult:
        found_types = []
        
        for pii_type, regex in self._compiled.items():
            if regex.search(content):
                found_types.append(pii_type)
        
        if found_types:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                severity=self._severity,
                reason=f"PII detected: {', '.join(found_types)}",
                metadata={"pii_types": found_types}
            )
        
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )


class ToolAuthorizationGuard(Guardrail):
    """
    Verify tool calls are authorized.
    
    This guardrail checks tool names and arguments against
    allowed/blocked lists and argument patterns.
    """
    
    def __init__(
        self,
        allowed_tools: Optional[Set[str]] = None,
        blocked_tools: Optional[Set[str]] = None,
        blocked_arg_patterns: Optional[Dict[str, List[str]]] = None,
        severity: GuardrailSeverity = GuardrailSeverity.CRITICAL
    ):
        """
        Args:
            allowed_tools: Whitelist of allowed tool names
            blocked_tools: Blacklist of blocked tool names
            blocked_arg_patterns: Dict of tool_name -> list of blocked arg patterns
            severity: Severity when unauthorized tool is detected
        """
        self._allowed = set(t.lower() for t in allowed_tools) if allowed_tools else None
        self._blocked = set(t.lower() for t in blocked_tools) if blocked_tools else set()
        self._blocked_args = blocked_arg_patterns or {}
        self._compiled_args = {
            tool: [re.compile(p, re.IGNORECASE) for p in patterns]
            for tool, patterns in self._blocked_args.items()
        }
        self._severity = severity
    
    @property
    def name(self) -> str:
        return "tool_authorization"
    
    def check(self, content: str) -> GuardrailResult:
        """
        Check if content contains unauthorized tool usage.
        
        Note: This is a simple pattern-based check. For actual tool calls,
        use check_tool() method directly.
        """
        # Simple heuristic: look for tool-like patterns
        tool_patterns = [
            r"(?:calling|using|executing)\s+tool[:\s]+(\w+)",
            r"tool_name[\"']?\s*:\s*[\"']?(\w+)",
        ]
        
        for pattern in tool_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                tool_name = match.group(1).lower()
                result = self.check_tool(tool_name, content)
                if result.triggered:
                    return result
        
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )
    
    def check_tool(self, tool_name: str, args: Optional[str] = None) -> GuardrailResult:
        """
        Directly check a tool call.
        
        Args:
            tool_name: Name of the tool being called
            args: Serialized arguments (for pattern matching)
        """
        tool_lower = tool_name.lower()
        
        # Check blacklist
        if tool_lower in self._blocked:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                severity=self._severity,
                reason=f"Tool '{tool_name}' is blocked",
                metadata={"tool": tool_name}
            )
        
        # Check whitelist
        if self._allowed is not None and tool_lower not in self._allowed:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                severity=self._severity,
                reason=f"Tool '{tool_name}' is not authorized",
                metadata={"tool": tool_name}
            )
        
        # Check arg patterns
        if args and tool_lower in self._compiled_args:
            for pattern in self._compiled_args[tool_lower]:
                if pattern.search(args):
                    return GuardrailResult(
                        guardrail_name=self.name,
                        triggered=True,
                        severity=self._severity,
                        reason=f"Blocked argument pattern in tool '{tool_name}'",
                        matched_pattern=pattern.pattern,
                        metadata={"tool": tool_name}
                    )
        
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )


class ContentLengthGuard(Guardrail):
    """Guard against excessively long content."""
    
    def __init__(
        self, 
        max_length: int = 100000,
        severity: GuardrailSeverity = GuardrailSeverity.WARNING
    ):
        self._max_length = max_length
        self._severity = severity
    
    @property
    def name(self) -> str:
        return "content_length"
    
    def check(self, content: str) -> GuardrailResult:
        if len(content) > self._max_length:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                severity=self._severity,
                reason=f"Content exceeds maximum length ({len(content)}/{self._max_length})",
                metadata={"length": len(content), "max": self._max_length}
            )
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )


class CodeExecutionGuard(Guardrail):
    """Detect potential dangerous code execution patterns."""
    
    DANGEROUS_PATTERNS = [
        r"\bexec\s*\(",
        r"\beval\s*\(",
        r"\bos\.system\s*\(",
        r"\bsubprocess\.",
        r"\b__import__\s*\(",
        r"\bopen\s*\([^)]*,\s*['\"]w",  # Writing files
        r"\brm\s+-rf\b",
        r"\bdel\s+/",
        r"\bformat\s+c:",
    ]
    
    def __init__(self, severity: GuardrailSeverity = GuardrailSeverity.CRITICAL):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._severity = severity
    
    @property
    def name(self) -> str:
        return "code_execution"
    
    def check(self, content: str) -> GuardrailResult:
        for pattern, regex in zip(self.DANGEROUS_PATTERNS, self._compiled):
            if regex.search(content):
                return GuardrailResult(
                    guardrail_name=self.name,
                    triggered=True,
                    severity=self._severity,
                    reason="Potentially dangerous code pattern detected",
                    matched_pattern=pattern
                )
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False
        )
