# emocore/escalation.py
"""
NOTE:
This component is downstream of Governance Kernel.
It must NOT influence kernel state, failure, or recovery.

EscalationResolver interprets budget values to determine escalation level,
but it does not modify kernel internals.
"""
from enum import Enum


class EscalationLevel(Enum):
    NORMAL = 0
    RETRYING = 1
    BACKING_OFF = 2
    COOLDOWN = 3
    HALT = 4
class EscalationResolver:
    def resolve(
        self,
        can_try: bool,
        backoff_delay: float,
        cooldown_active: bool,
        effort:float,
    ) -> EscalationLevel:
        if effort <= 0.05:
            return EscalationLevel.HALT
        if cooldown_active:
            return EscalationLevel.COOLDOWN
        if backoff_delay > 0.0:
            return EscalationLevel.BACKING_OFF
        if can_try:
            return EscalationLevel.RETRYING
        return EscalationLevel.NORMAL
