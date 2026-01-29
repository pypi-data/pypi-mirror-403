# emocore/behavior.py
"""
Behavior budget: EmoCore's output representing permission to act.

BehaviorBudget is the ONLY output of EmoCore that downstream systems should consume.
It represents *permission*, not *action*. Downstream control primitives decide
how to translate permission into actual behavior.

Budget dimensions:
- effort: How much work the agent is permitted to expend
- risk: How much uncertainty the agent may accept
- exploration: How much novelty-seeking is permitted
- persistence: How many retries/continuation attempts are allowed

All dimensions are in [0, 1] after clipping.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class BehaviorBudget:
    """
    Immutable budget representing behavioral permission.
    
    This is EmoCore's output. It represents how much the agent is
    permitted to do, not what the agent should do.
    
    EmoCore regulates permission. Control primitives decide execution.
    """
    effort: float
    risk: float
    persistence: float
    exploration: float


class BehaviorGate:
    """
    NOTE: This is a downstream control primitive.
    It must NOT influence EmoCore state, failure, or recovery.
    
    BehaviorGate applies budget constraints to action parameters.
    It consumes BehaviorBudget, it does not produce or modify it.
    """
    def apply(self, budget: BehaviorBudget, action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply budget constraints to action parameters."""
        a = action.copy()
        if "steps" in a:
            a["steps"] = max(1, int(a["steps"] * budget.effort))
        if budget.exploration == 0.0:
            if "allow_exploration" in a:
                a["allow_exploration"] = False
        if "max_risk" in a:
            a["max_risk"] = min(a["max_risk"], budget.risk)
        if "max_retries" in a:
            a["max_retries"] = max(1, int(a["max_retries"] * budget.persistence))
        return a
