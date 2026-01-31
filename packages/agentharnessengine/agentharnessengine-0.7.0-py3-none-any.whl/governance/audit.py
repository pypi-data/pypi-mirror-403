
"""
Audit System for Governance Kernel.

Records an immutable, append-only log of every governance decision and action attempt.
Essential for reconstructability and compliance.
"""

import json
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from governance.result import EngineResult

@dataclass
class AuditEntry:
    """
    Immutable record of a single governance event.
    """
    timestamp: str
    step: int
    action: str
    params: Dict[str, Any]
    signals: Dict[str, float]
    budget_snapshot: Dict[str, float]
    decision_halted: bool
    halt_reason: Optional[str]
    
    # Optional: Full state snapshot if needed, but budget is usually sufficient
    # mode: str

class AuditLogger:
    """
    In-memory audit logger.
    """
    def __init__(self):
        self._entries: List[AuditEntry] = []

    def log(self, 
            step: int, 
            action: str, 
            params: Dict[str, Any], 
            signals: Dict[str, float], 
            result: EngineResult) -> None:
        """
        Record a governance event.
        
        Args:
            step: Current harness step
            action: Name of the action being attempted
            params: Parameters for the action
            signals: The input signals passed to kernel
            result: The output result from kernel
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            step=step,
            action=action,
            params=params,
            signals=signals,
            budget_snapshot=dataclasses.asdict(result.budget),
            decision_halted=result.halted,
            halt_reason=result.reason
        )
        self._entries.append(entry)

    def dump(self) -> List[Dict[str, Any]]:
        """
        Return all entries as a list of dictionaries (JSON-serializable).
        """
        return [dataclasses.asdict(entry) for entry in self._entries]

    def dump_json(self, filepath: Optional[str] = None) -> str:
        """
        Serialize to JSON string, optionally writing to a file.
        """
        data = self.dump()
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
                
        return json_str
