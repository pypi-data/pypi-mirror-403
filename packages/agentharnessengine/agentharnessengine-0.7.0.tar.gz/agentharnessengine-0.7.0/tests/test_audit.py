
import pytest
import json
from governance.audit import AuditLogger
from governance.result import EngineResult
from governance.behavior import BehaviorBudget
from governance.modes import Mode
from governance.failures import FailureType

@pytest.fixture
def logger():
    return AuditLogger()

def test_audit_records_decision(logger):
    """Test logging an entry."""
    decision = EngineResult(
        state=None,
        budget=BehaviorBudget(0.9, 0.1, 0.9, 0.1),
        halted=False,
        failure=FailureType.NONE,
        reason=None,
        mode=Mode.IDLE
    )
    
    signals = {"reward": 0.5}
    params = {"prompt": "hello"}
    
    logger.log(
        step=1,
        action="llm_call",
        params=params,
        signals=signals,
        result=decision
    )
    
    dump = logger.dump()
    assert len(dump) == 1
    entry = dump[0]
    
    assert entry['step'] == 1
    assert entry['action'] == "llm_call"
    assert entry['decision_halted'] is False
    assert entry['budget_snapshot']['effort'] == 0.9

def test_audit_dump_json(logger, tmp_path):
    """Test JSON serialization."""
    decision = EngineResult(
        state=None,
        budget=BehaviorBudget(0.0, 0.0, 0.0, 0.0),
        halted=True,
        failure=FailureType.EXHAUSTION,
        reason="tired",
        mode=Mode.HALTED
    )
    
    logger.log(1, "act", {}, {}, decision)
    
    # Test string dump
    json_str = logger.dump_json()
    data = json.loads(json_str)
    assert data[0]['halt_reason'] == "tired"
    
    # Test file dump
    log_file = tmp_path / "audit.json"
    logger.dump_json(str(log_file))
    
    with open(log_file) as f:
        loaded = json.load(f)
        assert loaded[0]['halt_reason'] == "tired"
