import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from emocore.agent import EmoCoreAgent
from emocore.failures import FailureType
from emocore.profiles import ProfileType, PROFILES
def test_failure_enum_present_on_halt():
    agent = EmoCoreAgent()
    
    out = None
    for _ in range(20):
        out = agent.step(reward=0.0, novelty=0.0, urgency=0.0)
        if out.halted:
            break

    assert out.failure != FailureType.NONE
def test_post_failure_is_sticky():
    agent = EmoCoreAgent(profile=PROFILES[ProfileType.CONSERVATIVE])

    # Force exhaustion
    for _ in range(500):
        res = agent.step(0.0, 0.0, 0.0)
        if res.halted:
            break

    assert res.halted is True

    # Call again
    res2 = agent.step(1.0, 1.0, 1.0)

    assert res2.halted is True
    assert res2.budget.effort == 0.0
    assert res2.failure == res.failure
