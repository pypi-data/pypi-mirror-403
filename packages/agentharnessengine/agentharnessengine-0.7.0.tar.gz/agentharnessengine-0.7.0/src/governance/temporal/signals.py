# emocore/temporal/signals.py
"""
Temporal signal processors.

NOTE: StagnationDetector is NOT used in the v0.5 base prototype.

The base prototype uses GovernanceEngine-level stagnation detection via:
- GovernanceEngine.no_progress_steps counter
- Profile.stagnation_window threshold

This class is preserved for potential future use but is not wired
into the core governance loop. Do NOT integrate it without updating
the stagnation semantics documentation.
"""


class StagnationDetector:
    """
    NOT USED IN BASE PROTOTYPE.
    
    GovernanceEngine-level stagnation detection is authoritative.
    This class exists for experimental/future use only.
    """
    def __init__(self, window: int = 5, epsilon: float = 0.01):
        self.window = window
        self.epsilon = epsilon
        self.history = []

    def update_progress(self, value: float):
        self.history.append(value)
        if len(self.history) > self.window:
            self.history.pop(0)

    def is_stagnating(self) -> bool:
        if len(self.history) < self.window:
            return False
        return (max(self.history) - min(self.history)) <= self.epsilon
