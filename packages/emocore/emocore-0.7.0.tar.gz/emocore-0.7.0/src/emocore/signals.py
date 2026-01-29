from dataclasses import dataclass

@dataclass(frozen=True)
class Signals:
    reward: float
    novelty: float = 0.0
    urgency: float = 0.0
    difficulty: float = 0.0
    trust: float = 1.0  # Credibility of the evidence source
