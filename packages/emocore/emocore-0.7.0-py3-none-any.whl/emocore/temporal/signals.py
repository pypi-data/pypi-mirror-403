# emocore/temporal/signals.py
"""
Temporal signal processors.

NOTE: StagnationDetector is NOT used in the v0.5 base prototype.

The base prototype uses Engine-level stagnation detection via:
- Engine.no_progress_steps counter
- Profile.stagnation_window threshold

This class is preserved for potential future use but is not wired
into the core EmoCore loop. Do NOT integrate it without updating
the stagnation semantics documentation.
"""


class StagnationDetector:
    """
    NOT USED IN BASE PROTOTYPE.
    
    Engine-level stagnation detection is authoritative for v0.5.
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
