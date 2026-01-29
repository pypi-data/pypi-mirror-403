# emocore/temporal/controls.py
"""
Control primitives.

These consume BehaviorBudget outputs produced by EmoCore.
They must not influence EmoCore state, failure, recovery, or governance.

EmoCore regulates *permission to act*.
Control primitives decide *how actions are executed* downstream.

These classes are NOT part of EmoCore's core loop. They are utilities
for downstream systems that consume EmoCore's output.
"""
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """
    NOTE: This is a downstream control primitive.
    It must NOT influence EmoCore state, failure, or recovery.
    """
    def __init__(self, max_retries: int):
        self.max_retries = max_retries
        self.attempts = 0

    def allow_retry(self) -> bool:
        return self.attempts < self.max_retries

    def record_attempt(self):
        self.attempts += 1


class BackoffSchedule:
    def __init__(self, base_delay: float = 1.0, factor: float = 2.0):
        self.base_delay = base_delay
        self.factor = factor

    def delay(self, attempt: int) -> float:
        return self.base_delay * (self.factor ** (attempt - 1))


class CooldownGate:
    def __init__(self, cooldown_steps: int):
        self.cooldown_steps = cooldown_steps
        self.remaining = 0

    def trigger(self):
        self.remaining = self.cooldown_steps

    def step(self):
        if self.remaining > 0:
            self.remaining -= 1

    def allow_action(self) -> bool:
        return self.remaining == 0
