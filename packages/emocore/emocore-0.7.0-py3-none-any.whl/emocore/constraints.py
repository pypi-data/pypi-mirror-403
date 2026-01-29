"""
QUARANTINED: This module is deprecated and should not be used.

ConstraintEngine is broken and violates core EmoCore invariants:
- Checks for pressure values in [0, 1] but EmoCore allows UNBOUNDED pressure
- Uses snapshot() method that doesn't exist on PressureState
- Duplicates stagnation detection that belongs in Engine

DO NOT USE THIS MODULE. It is preserved only for reference.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataclasses import dataclass
from typing import List
from emocore.state import PressureState
from collections import deque

@dataclass(frozen=True)
class Violation:
    name: str
    description: str


class ConstraintEngine:
    """
    ⚠️ DEPRECATED: Do not use.
    
    This class is broken and violates EmoCore's unbounded pressure rule.
    Pressure values are NOT bounded to [0, 1] in EmoCore.
    
    This module is quarantined and preserved only for reference.
    """
    F_DOMINANCE = 0.75
    
    def validate_state(self, state: PressureState) -> List[Violation]:
        """DEPRECATED: Do not use."""
        violations = []
        
        # BROKEN: Assumes pressure is bounded, but EmoCore has unbounded pressure
        # This check is incorrect and should not be used
        # pressures = state.snapshot()  # snapshot() doesn't exist
        # for name, value in pressures.items():
        #     if value < 0.0 or value > 1.0:
        #         violations.append(...)
        
        # Check for frustration dominance
        if state.frustration > self.F_DOMINANCE:
            violations.append(Violation(
                name="dominance_violation",
                description=f"Frustration {state.frustration} exceeds dominance threshold {self.F_DOMINANCE}"
            ))
            
        return violations
        
    def __init__(self, window=10, epsilon=0.01):
        """DEPRECATED: Stagnation detection belongs in Engine, not ConstraintEngine."""
        self.progress_history = deque(maxlen=window)
        self.window = window
        self.epsilon = epsilon
        
    def update_progress(self, delta: float):
        """DEPRECATED: Do not use."""
        self.progress_history.append(delta)
        
    def is_stagnating(self) -> bool:
        """DEPRECATED: Use Engine's built-in stagnation detection instead."""
        if len(self.progress_history) < self.window:
            return False
        return sum(self.progress_history) <= self.epsilon
