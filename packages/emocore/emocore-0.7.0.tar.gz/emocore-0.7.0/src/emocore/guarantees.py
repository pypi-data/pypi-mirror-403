# emocore/guarantees.py
"""
Guarantee enforcement layer for EmoCore.

IMPORTANT: Guarantees enforce invariants, not semantics.

Guarantees:
- Budget values are always clamped to [0.0, 1.0]
- halted == True => budget is zeroed
- halted == True => mode == HALTED (no exceptions)

Guarantees do NOT:
- Decide when to halt
- Override failure semantics
- Modify pressure state
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import dataclass
from typing import Mapping, Optional, Dict
from emocore.behavior import BehaviorBudget
from emocore.modes import Mode
from emocore.failures import FailureType


# Type alias for external pressure snapshot
# Core uses PressureState internally; interface exposes this snapshot type
PressureSnapshot = Mapping[str, float]


@dataclass(frozen=True)
class StepResult:
    """
    Immutable result exposed by the public interface.
    
    NOTE: state is a PressureSnapshot (Mapping[str, float]), NOT a PressureState.
    PressureState is internal to core. The interface exposes a dict snapshot.
    """
    state: PressureSnapshot  # Dict snapshot, not PressureState
    budget: BehaviorBudget
    halted: bool
    failure: FailureType
    reason: str | None
    mode: Mode
    pressure_log: Optional[Dict[str, float]] = None  # Observability for debugging


class GuaranteeEnforcer:
    """
    Guarantees never decide. They only enforce invariants.
    
    Invariants enforced:
    1. Budget values clamped to [0.0, 1.0]
    2. halted == True => budget is zeroed
    3. halted == True => mode == HALTED
    
    CRITICAL: Failure and reason are ALWAYS preserved.
    Guarantees do NOT erase failure semantics.
    """

    def enforce(self, result: StepResult) -> StepResult:
        # HARD guarantee: budget bounded to [0.0, 1.0]
        b = result.budget
        safe_budget = BehaviorBudget(
            effort=min(max(b.effort, 0.0), 1.0),
            risk=min(max(b.risk, 0.0), 1.0),
            exploration=min(max(b.exploration, 0.0), 1.0),
            persistence=min(max(b.persistence, 0.0), 1.0),
        )

        if result.halted:
            # HARD guarantee: halted => zero budget, mode == HALTED
            # PRESERVE failure and reason (do NOT erase)
            return StepResult(
                state=result.state,
                budget=BehaviorBudget(0.0, 0.0, 0.0, 0.0),
                halted=True,
                failure=result.failure,  # Preserved
                reason=result.reason,     # Preserved (may be None, that's OK)
                mode=Mode.HALTED,         # INVARIANT: halted => HALTED
                pressure_log=result.pressure_log,  # Preserved
            )

        # Not halted: clamp budget only, preserve ALL other fields
        return StepResult(
            state=result.state,
            budget=safe_budget,
            halted=False,
            failure=result.failure,  # Preserved (not erased to NONE)
            reason=result.reason,    # Preserved (not erased to None)
            mode=result.mode,        # Preserved (not overridden)
            pressure_log=result.pressure_log,  # Preserved
        )
