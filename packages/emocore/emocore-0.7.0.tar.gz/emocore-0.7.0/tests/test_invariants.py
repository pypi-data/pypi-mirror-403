import time
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from emocore.state import PressureState
from emocore.governance import GovernanceEngine
from emocore.profiles import Profile

def test_pressure_never_decays():
    p = PressureState(confidence=1.0)
    p2 = p.integrate(PressureState())  # Zero delta
    time.sleep(0.1)
    assert p2.confidence == 1.0

def test_governance_is_stateless():
    g = GovernanceEngine(profile=None)
    p = PressureState(confidence=1.0)
    b1 = g.compute(p)
    b2 = g.compute(p)
    assert b1 == b2
