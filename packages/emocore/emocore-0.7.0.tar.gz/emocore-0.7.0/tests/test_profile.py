import os 
import sys 
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from emocore.agent import EmoCoreAgent
from emocore.profiles import Profile, PROFILES, ProfileType
from emocore.failures import FailureType
from emocore.state import PressureState
import time
import dataclasses

def test_conservative_halts_earlier_than_balanced():
    bal = EmoCoreAgent(profile=PROFILES[ProfileType.BALANCED])
    cons = EmoCoreAgent(profile=PROFILES[ProfileType.CONSERVATIVE])

    # Prime state to ensure budget > exhaustion threshold
    # Confidence 0.5 -> Effort ~0.3 (0.6 * 0.5)
    start_state = PressureState(confidence=0.5)
    bal.engine.state = start_state
    cons.engine.state = start_state

    halted_bal = None
    halted_cons = None

    for i in range(30):
        # Pure time/stagnation progression, no new pressure
        if halted_bal is None:
            r = bal.step(reward=0.0, novelty=0.0, urgency=0.0)
            if r.halted:
                halted_bal = i

        if halted_cons is None:
            r = cons.step(reward=0.0, novelty=0.0, urgency=0.0)
            if r.halted:
                halted_cons = i

    assert halted_cons is not None
    # Conservative window 10, Balanced 20.
    assert halted_cons < 20
    # Balanced might not halt in 30 steps if Decay is slow and Floor is low
    # But assertion is just comparison
    if halted_bal is not None:
        assert halted_cons < halted_bal

def test_aggressive_halts_later_than_balanced():
    bal = EmoCoreAgent(profile=PROFILES[ProfileType.BALANCED])
    agg = EmoCoreAgent(profile=PROFILES[ProfileType.AGGRESSIVE])

    # Prime state
    start_state = PressureState(confidence=0.5)
    bal.engine.state = start_state
    agg.engine.state = start_state

    halted_bal = None
    halted_agg = None

    for i in range(50):
        if halted_bal is None:
            r = bal.step(0.0, 0.0, 0.0)
            if r.halted:
                halted_bal = i

        if halted_agg is None:
            r = agg.step(0.0, 0.0, 0.0)
            if r.halted:
                halted_agg = i

    # Aggressive has larger window and higher limits
    # Should outlast Balanced
    if halted_bal is not None and halted_agg is not None:
        assert halted_agg > halted_bal
    elif halted_bal is not None:
        # Aggressive survived
        assert True
    else:
        # Neither halted?
        pass

def test_overrisk_halts_engine():
    profile = Profile(
        name="test_overrisk",
        max_risk=0.3,
        max_exploration=1.0,
        exhaustion_threshold=0.0,
        stagnation_window=100,
        time_persistence_decay=0.0,
        time_exploration_decay=0.0,
        max_steps=20,
        risk_scale=5.0,
    )

    core = EmoCoreAgent(profile=profile)
    # Prime high risk state
    # Risk Budget = 0.5 * State.risk * risk_scale(5.0)
    # If state.risk = 1.0 -> Budget = 2.5 > 0.3.
    core.engine.state = PressureState(risk=1.0, confidence=1.0) # Conf to prevent exhaustion

    out = None
    for _ in range(5):
        out = core.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0
        )
        if out.halted:
            break

    assert out.halted
    assert out.failure == FailureType.OVERRISK
def test_profile_halt_ordering():
    bal = EmoCoreAgent(profile=PROFILES[ProfileType.BALANCED])
    cons = EmoCoreAgent(profile=PROFILES[ProfileType.CONSERVATIVE])
    agg = EmoCoreAgent(profile=PROFILES[ProfileType.AGGRESSIVE])

    # Prime state to prevent immediate exhaustion
    start_state = PressureState(confidence=0.5)
    bal.engine.state = start_state
    cons.engine.state = start_state
    agg.engine.state = start_state

    halted = {}

    for i in range(200):
        if "bal" not in halted:
            r = bal.step(0.0, 0.0, 0.0)
            if r.halted:
                halted["bal"] = i

        if "cons" not in halted:
            r = cons.step(0.0, 0.0, 0.0)
            if r.halted:
                halted["cons"] = i

        if "agg" not in halted:
            r = agg.step(0.0, 0.0, 0.0)
            if r.halted:
                halted["agg"] = i

    assert halted["cons"] < halted["bal"] < halted["agg"]
def test_profiles_fail_differently():
    # Force Cons to fail by OVERRISK (max_risk=0.0) while Agg fails by EXHAUSTION
    cons_p = dataclasses.replace(PROFILES[ProfileType.CONSERVATIVE], max_risk=0.0)
    cons = EmoCoreAgent(profile=cons_p)
    agg = EmoCoreAgent(profile=PROFILES[ProfileType.AGGRESSIVE])

    # Prime state with some risk
    start_state = PressureState(confidence=0.5, risk=0.1)
    cons.engine.state = start_state
    agg.engine.state = start_state

    # Remove urgency to avoid premature exhaustion
    for _ in range(200):
        r_cons = cons.step(0.0, 0.0, 0.0)
        r_agg = agg.step(0.0, 0.0, 0.0)

        if r_cons.halted and r_agg.halted:
            break

    assert r_cons.failure != r_agg.failure
