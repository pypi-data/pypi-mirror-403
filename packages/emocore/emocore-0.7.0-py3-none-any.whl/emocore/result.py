import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from emocore.behavior import BehaviorBudget
from emocore.failures import FailureType
from emocore.modes import Mode


@dataclass(frozen=True)
class EngineResult:
    """
    Immutable result of a single EmoEngine step.
    This is the ONLY thing allowed to cross engine boundaries.
    """

    state: Optional[object]
    budget: BehaviorBudget
    halted: bool
    failure: FailureType
    reason: Optional[str]
    mode: Mode
    pressure_log: Optional[Dict[str, float]] = None  # Snapshot of current pressure values
