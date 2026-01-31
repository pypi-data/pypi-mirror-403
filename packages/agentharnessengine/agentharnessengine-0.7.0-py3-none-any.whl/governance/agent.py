# emocore/agent.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from governance.kernel import GovernanceEngine
from governance.profiles import Profile, PROFILES, ProfileType


class EmoCoreAgent:
    """
    Main entry point for the governance system.
    
    Acts as a facade over the internal GovernanceEngine.
    Preserves the name 'EmoCoreAgent' for compatibility, but uses
    engineering terminology internally.
    """
    def __init__(self, profile: Profile = PROFILES[ProfileType.BALANCED]):
        self.engine = GovernanceEngine(profile)

    def step(self, reward: float, novelty: float, urgency: float, difficulty: float = 0.0, trust: float = 1.0):
        """Execute one governance step."""
        return self.engine.step(reward, novelty, urgency, difficulty, trust)

    def reset(self, reason: str) -> None:
        """Reset the agent from a HALTED state. See GovernanceEngine.reset for semantics."""
        self.engine.reset(reason)


# Backward compatibility alias
EmoAgent = EmoCoreAgent
