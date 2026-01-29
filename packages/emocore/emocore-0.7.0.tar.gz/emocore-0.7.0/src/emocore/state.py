from dataclasses import dataclass

@dataclass(frozen=True)
class PressureState:
    """
    Canonical pressure axes.

    These fields are REQUIRED by AppraisalEngine and GovernanceEngine.
    No component may add, remove, or rename axes without breaking core invariants.

    These pressures represent accumulated internal state and are:
    - unbounded (can exceed [0, 1])
    - non-decaying (never decrease on their own)
    - not directly controllable (only influenced by appraisal)
    
    Axes:
    - confidence: Belief in ability to succeed
    - frustration: Accumulated negative affect from obstacles
    - curiosity: Drive to explore and learn
    - arousal: General activation/energy level
    - risk: Perceived danger or uncertainty
    
    This class is INTERNAL to core. External consumers receive PressureSnapshot
    (a Mapping[str, float]) via the public interface.
    """
    confidence: float = 0.0
    frustration: float = 0.0
    curiosity: float = 0.0
    arousal: float = 0.0
    risk: float = 0.0

    def integrate(self, delta: "PressureState") -> "PressureState":
        """
        Pure integration of pressure deltas.
        
        Args:
            delta: A PressureState containing delta values to add.
        
        Returns:
            New PressureState with deltas integrated.
        
        Invariants:
        - No decay
        - No clipping
        - No recovery
        - No mutation
        """
        return PressureState(
            confidence=self.confidence + delta.confidence,
            frustration=self.frustration + delta.frustration,
            curiosity=self.curiosity + delta.curiosity,
            arousal=self.arousal + delta.arousal,
            risk=self.risk + delta.risk,
        )
