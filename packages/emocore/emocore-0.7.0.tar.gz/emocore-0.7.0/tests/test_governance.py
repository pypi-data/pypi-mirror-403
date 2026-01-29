import pytest
import numpy as np
import os; import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from emocore.governance import GovernanceEngine
from emocore.state import PressureState
from emocore.behavior import BehaviorBudget

def test_governance_pure_function():
    gov = GovernanceEngine()
    state = PressureState(confidence=1.0, frustration=0.0)
    
    # First call
    budget1 = gov.compute(state)
    
    # Second call - same input -> same output
    budget2 = gov.compute(state)
    
    assert budget1 == budget2
    # Ensure it returns BehaviorBudget
    assert isinstance(budget1, BehaviorBudget)

def test_governance_no_momentum_but_accepts_metaparameters():
    gov = GovernanceEngine()
    state = PressureState()
    
    # NOW it SHOULD accept stagnating and dt
    # This previously raised TypeError. Now it should succeed.
    b = gov.compute(state, stagnating=True, dt=0.5)
    assert isinstance(b, BehaviorBudget)

def test_governance_frustration_suppression():
    gov = GovernanceEngine()
    # High frustration should suppress curiosity (based on old F_DOM rule)
    state = PressureState(frustration=0.9, curiosity=1.0)
    
    budget = gov.compute(state)
    
    assert budget.exploration == 0.0
