import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


import time
from emocore.agent import EmoCoreAgent
from emocore.failures import FailureType
from emocore.modes import Mode
from emocore.profiles import PROFILES,ProfileType
#A. Infinite Loop Resistance

def test_infinite_loop_resistance():
    agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])

    out = None
    for _ in range(500):
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0,
        )
        if out.halted:
            break

    assert out is not None
    assert out.halted is True
    assert out.failure in {
        FailureType.EXHAUSTION,
        FailureType.STAGNATION,
    }
    assert out.mode == Mode.HALTED

#B. Adversarial Urgency Flood

def test_adversarial_urgency_flood():
    agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])

    out = None
    for _ in range(300):
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=1.0,
        )
        if out.halted:
            break

    assert out is not None
    assert out.halted is True
    assert out.failure in {
        FailureType.OVERRISK,
        FailureType.EXHAUSTION,
        FailureType.STAGNATION,
    }
    assert out.mode == Mode.HALTED

#C. Profile Divergence (Formal)

def test_profile_divergence_identical_inputs():
    agents = {
        "cons": EmoCoreAgent(PROFILES[ProfileType.CONSERVATIVE]),
        "bal": EmoCoreAgent(PROFILES[ProfileType.BALANCED]),
        "agg": EmoCoreAgent(PROFILES[ProfileType.AGGRESSIVE]),
    }

    halt_steps = {}

    for name, agent in agents.items():
        for step in range(500):
            out = agent.step(
                reward=0.0,
                novelty=0.1,
                urgency=0.2,
            )
            if out.halted:
                halt_steps[name] = step
                break

    assert halt_steps["cons"] < halt_steps["bal"] < halt_steps["agg"]

#D. Recovery Boundary Test

def test_recovery_boundary():
    agent = EmoCoreAgent(PROFILES[ProfileType.BALANCED])

    # Drive toward exhaustion
    for _ in range(50):
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0,
        )
        if out.mode == Mode.RECOVERING:
            break

    assert out.mode == Mode.RECOVERING

    effort_values = []
    risk_values = []

    for _ in range(20):
        time.sleep(0.05)
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0,
        )
        effort_values.append(out.budget.effort)
        risk_values.append(out.budget.risk)

    # Effort recovers but is bounded
    assert max(effort_values) <= 1.0

    # Risk never increases during recovery
    assert risk_values == sorted(risk_values, reverse=True)

#E. Post-Halt Integrity

def test_post_halt_integrity():
    agent = EmoCoreAgent(PROFILES[ProfileType.CONSERVATIVE])

    # Force halt
    for _ in range(200):
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=1.0,
        )
        if out.halted:
            break

    failure = out.failure

    # Keep stepping
    for _ in range(20):
        out2 = agent.step(
            reward=1.0,
            novelty=1.0,
            urgency=1.0,
        )

        assert out2.halted is True
        assert out2.failure == failure
        assert out2.budget.effort == 0.0
        assert out2.budget.risk == 0.0
        assert out2.mode == Mode.HALTED
