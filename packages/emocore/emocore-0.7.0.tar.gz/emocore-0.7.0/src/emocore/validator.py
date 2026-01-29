from dataclasses import dataclass, replace
from typing import List, Optional
from collections import deque
import math

from typing import List, Optional
from collections import deque
import math

from emocore.signals import Signals


class ValidationError(Exception):
    """Raised when strict validation fails."""
    pass

class SignalValidator:
    """
    Deterministically validates signals against specification invariants.
    
    Responsibilities:
    1. Range enforcement (Clamping)
    2. Smoothness checks (Max delta)
    3. Oscillation detection
    
    Modes:
    - strict=False (Default): Clamp values, log warnings (via return), continue.
    - strict=True: Raise ValidationError on any violation.
    """
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.last_signals: Optional[Signals] = None
        self.signal_history: deque = deque(maxlen=10)
        
    def validate(self, signals: Signals) -> Signals:
        """
        Validate and optionally sanitize signals.
        Returns a guaranteed valid Signals object.
        """
        # 1. Range Check & Clamping
        validated = self._enforce_ranges(signals)
        
        # 2. Smoothness Check (Delta Limiting)
        if self.last_signals:
            validated = self._enforce_smoothness(validated, self.last_signals)
            
        # 3. Oscillation Check
        self._check_oscillation(validated)
        
        # Update history
        self.last_signals = validated
        self.signal_history.append(validated)
        
        return validated
    
    def _enforce_ranges(self, s: Signals) -> Signals:
        """Enforce [-1, 1] for reward, [0, 1] for others."""
        r = s.reward
        n = s.novelty
        u = s.urgency
        d = s.difficulty  # Note: interface.Signals needs difficulty added
        
        # Check bounds
        violations = []
        if not (-1.0 <= r <= 1.0): violations.append(f"Reward {r} out of [-1, 1]")
        if not (0.0 <= n <= 1.0): violations.append(f"Novelty {n} out of [0, 1]")
        if not (0.0 <= u <= 1.0): violations.append(f"Urgency {u} out of [0, 1]")
        # Difficulty range check assumes [0,1] based on spec
        if hasattr(s, 'difficulty') and not (0.0 <= s.difficulty <= 1.0):
             violations.append(f"Difficulty {s.difficulty} out of [0, 1]")
             
        if violations and self.strict:
            raise ValidationError(f"Range violations: {violations}")
        
        # trust range check
        if not (0.0 <= s.trust <= 1.0):
            violations.append(f"Trust {s.trust} out of [0, 1]")
            
        # Clamp (always safe)
        d = s.difficulty
        return replace(s,
            reward=max(-1.0, min(1.0, r)),
            novelty=max(0.0, min(1.0, n)),
            urgency=max(0.0, min(1.0, u)),
            difficulty=max(0.0, min(1.0, d)),
            trust=max(0.0, min(1.0, s.trust))
        )
        
    def _enforce_smoothness(self, current: Signals, previous: Signals) -> Signals:
        """Enforce max delta of 0.5 per step."""
        MAX_DELTA = 0.5
        
        # Helper to clamp delta
        def smooth(curr, prev, name):
            delta = curr - prev
            if abs(delta) > MAX_DELTA:
                if self.strict:
                    raise ValidationError(f"{name} delta {delta} > {MAX_DELTA}")
                return prev + math.copysign(MAX_DELTA, delta)
            return curr

        # Difficulty might not be on Signals object yet in some phases
        # We need to be robust
        new_diff = 0.0
        if hasattr(current, 'difficulty') and hasattr(previous, 'difficulty'):
            new_diff = smooth(current.difficulty, previous.difficulty, "Difficulty")

        return replace(current,
            reward=smooth(current.reward, previous.reward, "Reward"),
            novelty=smooth(current.novelty, previous.novelty, "Novelty"),
            urgency=smooth(current.urgency, previous.urgency, "Urgency"),
            difficulty=smooth(current.difficulty, previous.difficulty, "Difficulty"),
            trust=smooth(current.trust, previous.trust, "Trust")
        )

    def _check_oscillation(self, current: Signals) -> None:
        """Check for rapid sign flipping (oscillation)."""
        # Combine history + current to check recent trend including this step
        recent = list(self.signal_history) + [current]
        
        if len(recent) < 5:
            return
            
        # Check reward oscillation (sign flips)
        flips = 0
        for i in range(1, len(recent)):
            prev = recent[i-1].reward
            curr = recent[i].reward
            if (prev > 0 and curr < 0) or (prev < 0 and curr > 0):
                flips += 1
                
        if flips > 3:
            if self.strict:
                raise ValidationError(f"Reward oscillation validation failed: {flips} flips in history")
            # In non-strict, we allow it but Extractor trust logic handles it
