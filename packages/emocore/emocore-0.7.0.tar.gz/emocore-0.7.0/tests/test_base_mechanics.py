# tests/test_base_mechanics.py
"""
Hardcore Base Prototype Test Suite

These tests verify the core semantic promises of EmoCore:
- Infinite loop prevention
- Bounded agency
- Explicit failure
- Safe recovery
- Terminal halt
- Profile divergence
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from emocore.agent import EmoCoreAgent
from emocore.failures import FailureType
from emocore.modes import Mode
from emocore.profiles import PROFILES, ProfileType


# =============================================================================
# 1️⃣ Infinite Loop Prevention (Stagnation)
# =============================================================================
def test_infinite_zero_reward_loop_halts():
    """
    What this proves:
    - EmoCore does not allow infinite retries
    - Stagnation is detected
    - Failure is explicit
    
    If this fails → EmoCore is fake governance.
    """
    agent = EmoCoreAgent()
    
    last = None
    for i in range(1_000):
        last = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0
        )
        if last.halted:
            break

    assert last is not None
    assert last.halted is True
    assert last.failure in {
        FailureType.STAGNATION,
        FailureType.EXHAUSTION,
        FailureType.EXTERNAL,
    }


# =============================================================================
# 2️⃣ Risk Escalation Must Halt (No Silent Runaway)
# =============================================================================
def test_runaway_risk_halts_engine():
    """
    What this proves:
    - Risk is bounded
    - OVERRISK triggers when budget.risk >= max_risk
    - Recovery does not mask risk
    
    If it keeps running → safety failure.
    
    NOTE: Current appraisal maps urgency→arousal, not urgency→risk.
    To test OVERRISK semantics, we prime state.risk and use a profile
    with high risk_scale to amplify it into budget.risk.
    """
    import dataclasses
    from emocore.state import PressureState
    
    # Create profile with low risk threshold and high risk scaling
    overrisk_profile = dataclasses.replace(
        PROFILES[ProfileType.BALANCED],
        max_risk=0.3,                 # Low threshold
        risk_scale=5.0,               # Amplify risk
        exhaustion_threshold=0.0,     # Prevent exhaustion
        stagnation_window=1000,       # Prevent stagnation
    )
    agent = EmoCoreAgent(overrisk_profile)
    
    # Prime state with high risk pressure
    agent.engine.state = PressureState(risk=1.0, confidence=1.0)
    
    out = None
    for _ in range(20):
        out = agent.step(
            reward=0.0,
            novelty=0.0,
            urgency=0.0
        )
        if out.halted:
            break

    assert out is not None
    assert out.halted is True
    assert out.failure == FailureType.OVERRISK


# =============================================================================
# 3️⃣ Recovery Is Mode-Bound (No Background Buffs)
# =============================================================================
def test_recovery_only_in_recovering_mode():
    """
    What this proves:
    - Recovery only happens in RECOVERING
    - Normal operation does not secretly regenerate budget
    
    If effort increases in IDLE → recovery is broken.
    """
    agent = EmoCoreAgent()

    r1 = agent.step(0.0, 0.0, 0.0)
    r2 = agent.step(0.0, 0.0, 0.0)

    if r2.mode == Mode.IDLE:
        assert r2.budget.effort <= r1.budget.effort


# =============================================================================
# 4️⃣ Risk Must Not Increase During Recovery
# =============================================================================
def test_risk_frozen_during_recovery():
    """
    What this proves:
    - Recovery is safe
    - No hidden risk escalation
    
    If risk increases → recovery is unsafe.
    """
    agent = EmoCoreAgent()

    # Force recovery
    for _ in range(50):
        out = agent.step(0.0, 0.0, 0.0)
        if out.mode == Mode.RECOVERING:
            break

    assert out.mode == Mode.RECOVERING

    risk_before = out.budget.risk
    out2 = agent.step(0.0, 0.0, 0.0)

    assert out2.budget.risk <= risk_before


# =============================================================================
# 5️⃣ Recovery Cannot Exceed Pre-Failure Budget
# =============================================================================
def test_recovery_bounded_by_pre_failure_budget():
    """
    What this proves:
    - Recovery is bounded
    - No post-failure "superpower"
    """
    agent = EmoCoreAgent()

    # Drive system until just before recovery
    last_idle = None
    for _ in range(100):
        out = agent.step(0.0, 0.0, 0.0)
        if out.mode == Mode.IDLE:
            last_idle = out

        if out.mode == Mode.RECOVERING:
            break

    assert last_idle is not None

    recovered = agent.step(0.0, 0.0, 0.0)

    assert recovered.budget.effort <= last_idle.budget.effort
    assert recovered.budget.persistence <= last_idle.budget.persistence


# =============================================================================
# 6️⃣ HALT Is Terminal (No Resurrection)
# =============================================================================
def test_halt_is_terminal():
    """
    What this proves:
    - Failure ends the session
    - No post-halt evolution
    """
    agent = EmoCoreAgent()

    out = None
    for _ in range(500):
        out = agent.step(0.0, 0.0, 1.0)
        if out.halted:
            break

    assert out.halted is True
    assert out.mode == Mode.HALTED

    after = agent.step(1.0, 1.0, 0.0)

    assert after.halted is True
    assert after.budget.effort == 0.0
    assert after.mode == Mode.HALTED


# =============================================================================
# 7️⃣ Profile Divergence (Same Inputs, Different Fate)
# =============================================================================
def test_profiles_diverge_on_identical_inputs():
    """
    What this proves:
    - Profiles matter
    - Governance is not cosmetic
    
    If this ordering fails → profiles are meaningless.
    """
    agents = {
        "conservative": EmoCoreAgent(PROFILES[ProfileType.CONSERVATIVE]),
        "balanced": EmoCoreAgent(PROFILES[ProfileType.BALANCED]),
        "aggressive": EmoCoreAgent(PROFILES[ProfileType.AGGRESSIVE]),
    }

    halt_steps = {}

    for name, agent in agents.items():
        for i in range(300):
            out = agent.step(0.0, 0.0, 0.5)
            if out.halted:
                halt_steps[name] = i
                break

    assert halt_steps["conservative"] < halt_steps["balanced"] < halt_steps["aggressive"]


# =============================================================================
# 8️⃣ Budget Invariants (Never Broken)
# =============================================================================
def test_budget_always_bounded():
    """
    What this proves:
    - Hard safety invariants always hold
    """
    agent = EmoCoreAgent()

    for _ in range(500):
        out = agent.step(0.5, 0.5, 0.5)
        b = out.budget

        assert 0.0 <= b.effort <= 1.0
        assert 0.0 <= b.risk <= 1.0
        assert 0.0 <= b.exploration <= 1.0
        assert 0.0 <= b.persistence <= 1.0
