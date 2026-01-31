from dataclasses import dataclass
from enum import Enum, auto


class ProfileType(Enum):
    """
    Canonical profile identifiers.
    Used only for lookup & selection.
    """
    BALANCED = auto()
    CONSERVATIVE = auto()
    AGGRESSIVE = auto()

@dataclass(frozen=True)
class Profile:
    """
    Immutable profile constants.

    Rules:
    - NO logic
    - NO mutation
    - Configuration only
    """

    name: str = "default"

    # --- Time decay ---
    time_persistence_decay: float = 0.0
    time_exploration_decay: float = 0.0

    # --- Time-based recovery ---
    recovery_rate:float = 0.0
    recovery_cap:float = 1.0
    recovery_delay:float = 0.0

    # --- Governance scaling ---
    effort_scale: float = 1.0
    risk_scale: float = 1.0
    exploration_scale: float = 1.0
    persistence_scale: float = 1.0

    # --- Step-based decay ---
    persistence_decay: float = 0.0
    exploration_decay: float = 0.0

    # --- Failure sensitivity ---
    stagnation_window: int = 10
    exhaustion_threshold: float = 0.2
    max_risk: float = 1.0
    max_exploration: float = 1.0
    max_steps: int = 1_000_000
    stagnation_effort_floor: float = 0.0
    stagnation_effort_scale: float = 1.0
    stagnation_persistence_scale: float = 1.0
    progress_threshold: float = 0.05


# =========================
# Canonical Profiles
# =========================

BALANCED = Profile(
    name="BALANCED",
    effort_scale=1.0,
    risk_scale=1.0,
    exploration_scale=1.0,
    persistence_scale=1.0,
    recovery_rate=0.25,
    recovery_cap=1.0,
    recovery_delay=0.5,
    persistence_decay=0.05,
    exploration_decay=0.05,
    time_persistence_decay=0.002,
    time_exploration_decay=0.002,
    stagnation_window=20,
    exhaustion_threshold=0.05,
    max_risk=1.0,
    max_exploration=1.0,
    max_steps=100,
    stagnation_effort_floor=0.1,
    stagnation_effort_scale=0.7,
    stagnation_persistence_scale=0.6,
)

CONSERVATIVE = Profile(
    name="CONSERVATIVE",
    effort_scale=0.9,
    risk_scale=0.6,
    exploration_scale=0.5,
    persistence_scale=0.9,
    recovery_rate=0.15,
    recovery_cap=1.0,
    recovery_delay=1.0,
    persistence_decay=0.08,
    exploration_decay=0.10,
    time_persistence_decay=0.004,
    time_exploration_decay=0.004,
    stagnation_window=10,
    exhaustion_threshold=0.1,
    max_risk=0.8,
    max_exploration=0.6,
    max_steps=60,
    stagnation_effort_floor=0.2,
    stagnation_effort_scale=0.5,
    stagnation_persistence_scale=0.4,
)

AGGRESSIVE = Profile(
    name="AGGRESSIVE",
    effort_scale=1.2,
    risk_scale=1.3,
    exploration_scale=1.4,
    persistence_scale=1.1,
    recovery_rate=0.50,
    recovery_cap=0.75,
    recovery_delay=0.2,
    persistence_decay=0.02,
    exploration_decay=0.02,
    time_persistence_decay=0.001,
    time_exploration_decay=0.001,
    stagnation_window=30,
    exhaustion_threshold=0.0,
    max_risk=1.5,
    max_exploration=1.5,
    max_steps=200,
    stagnation_effort_floor=0.05,
    stagnation_effort_scale=0.9,
    stagnation_persistence_scale=0.8,
)


# =========================
# Registry (read-only)
# =========================

PROFILES = {
    ProfileType.BALANCED: BALANCED,
    ProfileType.CONSERVATIVE: CONSERVATIVE,
    ProfileType.AGGRESSIVE: AGGRESSIVE,
}
