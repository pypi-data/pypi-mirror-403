# emocore/failures.py
"""
Failure types for EmoCore.

FailureType identifies WHY the engine halted. This is diagnostic information,
not a control signal. Downstream systems may use this for logging, recovery
decisions, or user feedback, but they must NOT use it to influence EmoCore state.

Failure types are:
- NONE: No failure (engine running normally)
- STAGNATION: No progress for too long (governance failure)
- EXHAUSTION: Effort depleted below threshold (governance failure)
- SAFETY: Exploration exceeded limits (governance failure)
- OVERRISK: Risk exceeded limits (governance failure)
- EXTERNAL: Step limit reached (safety fuse, NOT governance)
"""
from enum import Enum, auto


class FailureType(Enum):
    """
    Identifies why the engine halted.
    
    Governance failures (derived from pressure/budget):
    - STAGNATION: No progress, effort floor reached
    - EXHAUSTION: Effort depleted below threshold
    - SAFETY: Exploration exceeded maximum
    - OVERRISK: Risk exceeded maximum
    
    External failures (NOT governance):
    - EXTERNAL: Step limit reached (safety fuse)
    
    EXTERNAL is a safety fuse, not emotional regulation.
    It is not learned or adaptive. It is a hard limit.
    """
    NONE = auto()
    STAGNATION = auto()
    EXHAUSTION = auto()
    SAFETY = auto()
    EXTERNAL = auto()
    OVERRISK = auto()
