# emocore/appraisal.py
"""
AppraisalEngine: Converts environmental signals into pressure deltas.

What AppraisalEngine does:
- Takes reward, novelty, urgency signals from the environment
- Produces pressure DELTAS for all canonical axes
- These deltas are integrated into PressureState by the engine

What AppraisalEngine does NOT do:
- Detect stagnation (that's Engine's job)
- Respond to stagnation (that's Governance's job)
- Clip or bound pressures (PressureState is unbounded)
- Learn or adapt (coefficients are fixed)

Assumptions:
- Output must produce deltas for all 5 canonical pressure axes
- Deltas are additive (integrated via PressureState.integrate())
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict
from emocore.state import PressureState


class AppraisalEngine:
    """
    Appraisal engine that converts stimuli into pressure deltas.
    
    This is the input layer of EmoCore. It translates environmental
    signals into internal pressure changes.
    
    Boundary clarification:
    - Appraisal produces pressure DELTAS (not absolute values)
    - Appraisal does NOT detect stagnation (that's Engine's job)
    - Appraisal does NOT respond to stagnation (that's Governance's job)
    """
    
    def appraise(self, stimulus: Dict[str, float]) -> Dict[str, float]:
        """Internal appraisal from raw stimulus dict."""
        n = stimulus.get("novelty", 0.0)
        d = stimulus.get("difficulty", 0.0)
        p = stimulus.get("progress", 0.0)
        u = stimulus.get("urgency", 0.0)
        deltas = {
            "confidence": (p*0.3) - (d*0.1),
            "frustration": (0.0 if p > 0 else d*0.4)+ (u*0.2),
            "curiosity": (n*0.5) - ((1.0-n)*0.2),
            "arousal": u * 0.6,
            "risk": -abs(p)*0.3,
        }
        return deltas

    def compute(self, reward: float, novelty: float, urgency: float, difficulty: float = 0.1) -> PressureState:
        """
        Compute pressure delta from engine signals.
        
        Returns:
            PressureState containing delta values (not absolute pressures).
            This is passed directly to PressureState.integrate().
        """
        stimulus = {
            "progress": reward,  # Mapping reward to progress
            "novelty": novelty,
            "urgency": urgency,
            "difficulty": difficulty,
        }
        deltas = self.appraise(stimulus)
        return PressureState(
            confidence=deltas["confidence"],
            frustration=deltas["frustration"],
            curiosity=deltas["curiosity"],
            arousal=deltas["arousal"],
            risk=deltas["risk"],
        )
