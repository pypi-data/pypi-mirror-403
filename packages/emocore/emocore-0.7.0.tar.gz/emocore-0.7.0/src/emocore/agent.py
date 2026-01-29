# emocore/agent.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emocore.engine import EmoEngine
from emocore.profiles import Profile, PROFILES, ProfileType


class EmoCoreAgent:
    def __init__(self, profile: Profile = PROFILES[ProfileType.BALANCED]):
        self.engine = EmoEngine(profile)

    def step(self, reward: float, novelty: float, urgency: float, difficulty: float = 0.0, trust: float = 1.0):
        return self.engine.step(reward, novelty, urgency, difficulty, trust)

    def reset(self, reason: str) -> None:
        """Reset the agent from a HALTED state. See EmoEngine.reset for semantics."""
        self.engine.reset(reason)
