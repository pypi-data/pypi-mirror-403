# emocore/policy.py
"""
NOTE:
This component is downstream of EmoCore.
It must NOT influence EmoCore state, failure, or recovery.

ExternalPolicy and PolicyEnforcer apply external constraints to budgets,
but they do not modify EmoCore internals.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import dataclass
from emocore.behavior import BehaviorBudget

@dataclass
class ExternalPolicy:
    max_effort: float = 1.0
    max_risk: float = 1.0
    max_exploration: float = 1.0
    max_persistence: float = 1.0

class PolicyEnforcer:
    def apply(self, budget: BehaviorBudget, policy: ExternalPolicy) -> BehaviorBudget:
        return BehaviorBudget(
            effort=min(budget.effort, policy.max_effort),
            risk=min(budget.risk, policy.max_risk),
            exploration=min(budget.exploration, policy.max_exploration),
            persistence=min(budget.persistence, policy.max_persistence),
        )
