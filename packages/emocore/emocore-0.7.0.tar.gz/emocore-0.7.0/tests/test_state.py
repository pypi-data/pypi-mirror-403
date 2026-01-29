import pytest
import os; import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from emocore.state import PressureState

def test_state_immutable_integration():
    initial = PressureState()
    delta = PressureState(confidence=0.1, frustration=0.2)
    
    new_state = initial.integrate(delta)
    
    # Original should be unchanged
    assert initial.confidence == 0.0
    assert initial.frustration == 0.0
    
    # New state should have changes
    assert new_state.confidence == 0.1
    assert new_state.frustration == 0.2

def test_state_no_clipping_in_state():
    initial = PressureState(confidence=0.9)
    # Even if we add lot of pressure, state just accumulates
    delta = PressureState(confidence=0.5)
    new_state = initial.integrate(delta)
    assert new_state.confidence == 1.4

def test_state_no_decay_method():
    initial = PressureState()
    # Ensure there is no decay method
    assert not hasattr(initial, "decay")
    assert not hasattr(initial, "momentum")
