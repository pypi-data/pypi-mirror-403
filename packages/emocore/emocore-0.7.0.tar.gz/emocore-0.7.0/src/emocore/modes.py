# emocore/modes.py
"""
EmoCore operational modes.

Mode semantics:

IDLE        – normal operation, full governance applies
RECOVERING  – constrained operation, reduced agency, recovery allowed
HALTED      – terminal state, zero budget, no recovery or evolution

These modes are derived, not directly set. Mode is determined by:
- Budget thresholds (effort/persistence < 0.3 => RECOVERING)
- Failure conditions (any failure => HALTED)
- Default state (IDLE)

Modes are NOT:
- User-configurable at runtime
- Learning targets
- Action commands
"""
from enum import Enum, auto


class Mode(Enum):
    """
    Mode semantics:

    IDLE        – normal operation, full governance applies
    RECOVERING  – constrained operation, reduced agency, recovery allowed
    HALTED      – terminal state, zero budget, no recovery or evolution
    """
    IDLE = auto()
    RECOVERING = auto()
    HALTED = auto()
