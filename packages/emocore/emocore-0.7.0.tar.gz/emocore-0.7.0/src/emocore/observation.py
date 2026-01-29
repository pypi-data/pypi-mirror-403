from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Observation:
    """
    Represents an observable behavior snapshot from an agent.
    
    This is the universal contract between the outside world (via Adapters)
    and the EmoCore extraction layer. Adapters must convert domain-specific
    data (LLM responses, robot logs, etc.) into this format.
    
    Attributes:
        action (str): The name or identifier of the action taken.
        result (str): The outcome of the action ('success', 'failure', 'timeout', etc.).
        env_state_delta (float): Magnitude of change in the external environment [0.0, 1.0].
                                 Examples: File written, DB row updated, robot moved.
        agent_state_delta (float): Magnitude of change in the agent's internal state [0.0, 1.0].
                                   Examples: Reasoning tokens generated, memory updated.
        elapsed_time (float): Wall-clock time consumed by this step in seconds.
        tokens_used (int): Number of tokens consumed (for LLM agents). Defaults to 0.
        error (str | None): Error message if the result was a failure/error.
    """
    action: str
    result: str
    env_state_delta: float
    agent_state_delta: float
    elapsed_time: float
    tokens_used: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        # Lightweight validation to catch obvious adapter bugs early
        pass
