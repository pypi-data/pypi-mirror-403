# emocore/__init__.py
"""
EmoCore - Runtime Governance for Autonomous Agents

Public API:
    from emocore import EmoCoreAgent, step, Signals
    from emocore.profiles import PROFILES, ProfileType

Usage:
    agent = EmoCoreAgent()
    result = step(agent, Signals(reward=0.5, novelty=0.1, urgency=0.2))
"""

from emocore.agent import EmoCoreAgent
from emocore.interface import step, observe, Signals
from emocore.observation import Observation
from emocore.adapters import LLMLoopAdapter, ToolCallingAgentAdapter
from emocore.guarantees import StepResult, GuaranteeEnforcer
from emocore.failures import FailureType
from emocore.modes import Mode
from emocore.behavior import BehaviorBudget
from emocore.state import PressureState
from emocore.profiles import Profile, PROFILES, ProfileType

__all__ = [
    # Main API
    "EmoCoreAgent",
    "step",
    "observe",
    "Signals",
    "Observation",
    "StepResult",
    # Adapters
    "LLMLoopAdapter",
    "ToolCallingAgentAdapter",
    # Types
    "FailureType",
    "Mode",
    "BehaviorBudget",
    "PressureState",
    # Profiles
    "Profile",
    "PROFILES",
    "ProfileType",
    # Guarantees
    "GuaranteeEnforcer",
]

__version__ = "0.7.0"
