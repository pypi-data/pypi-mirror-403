# emocore/interface.py

from dataclasses import dataclass, asdict
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emocore.agent import EmoCoreAgent
from emocore.observation import Observation
from emocore.extractor import SignalExtractor, RuleBasedExtractor
from emocore.validator import SignalValidator
from emocore.guarantees import (
    GuaranteeEnforcer,
    StepResult,
)
from emocore.signals import Signals
from emocore.failures import FailureType
from emocore.modes import Mode



def step(agent: EmoCoreAgent, signals: Signals) -> StepResult:
    """
    Canonical public interface.
    Pure function: no mutation of inputs.
    """

    res = agent.step(
        reward=signals.reward,
        novelty=signals.novelty,
        urgency=signals.urgency,
        difficulty=signals.difficulty,
        trust=signals.trust,
    )

    # EngineResult → StepResult
    result = StepResult(
        state=asdict(res.state), # Snapshot dict for the interface
        budget=res.budget,
        halted=res.halted,
        failure=res.failure,
        reason=res.reason,
        mode=res.mode,
        pressure_log=res.pressure_log,  # Pass through from engine
    )

    # Enforce guarantees (clamp, override if halted)
    return GuaranteeEnforcer().enforce(result)


def observe(
    agent: EmoCoreAgent, 
    observation: Observation,
    extractor: SignalExtractor | None = None,
    validator: SignalValidator | None = None
) -> StepResult:
    """
    Primary API for Signal Specification v0.x (Path B).
    
    Ingests observable behavior (Observation), extracts signals using
    an Extractor (default: RuleBased), validates them, and executes
    deterministic governance.
    
    Args:
        agent: The EmoCore agent instance.
        observation: The behavioral evidence via an Adapter.
        extractor: Optional custom extractor. Defaults to RuleBasedExtractor.
        validator: Optional custom validator. Defaults to SignalValidator(strict=False).
        
    Returns:
        StepResult: The governance decision (halted, mode, etc.)
    """
    # 1. Select Extractor (maintain state across calls)
    if extractor is None:
        if not hasattr(agent, '_extractor'):
            agent._extractor = RuleBasedExtractor()
        extractor = agent._extractor

    # 2. Extract Signals (Heuristic Layer)
    signals = extractor.extract(observation)
    
    # 3. Validate Signals (Deterministic Layer)
    if validator is None:
        if not hasattr(agent, '_validator'):
            agent._validator = SignalValidator(strict=False)
        validator = agent._validator
    
    signals = validator.validate(signals)
    
    # 4. Governance (Deterministic Layer)
    return step(agent, signals)
