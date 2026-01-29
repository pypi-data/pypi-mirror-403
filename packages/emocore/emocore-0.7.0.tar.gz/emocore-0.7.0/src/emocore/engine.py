# emocore/engine.py
import os 
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from emocore.appraisal import AppraisalEngine
from emocore.governance import GovernanceEngine
from emocore.state import PressureState
from emocore.behavior import BehaviorBudget
from emocore.failures import FailureType
from emocore.modes import Mode
from emocore.result import EngineResult


class EmoEngine:
    """
    Core emotional engine that governs agent behavior through pressure dynamics.
    
    Post-Failure Lifecycle Semantics:
    ---------------------------------
    HALTED is TERMINAL for the session. Once the engine enters HALTED mode:
    
    - State does NOT evolve (pressure accumulation stops)
    - Governance does NOT run (no budget computation)
    - Recovery does NOT occur (no effort/persistence restoration)
    - Budget is permanently ZEROED for the session
    
    There is NO auto-recovery from HALTED. The session must be restarted
    to resume operation. This is a safety invariant, not a limitation.
    """
    
    # Budget inertia constant: controls smoothing across steps
    # Higher values = more weight on previous budget (smoother, slower response)
    # Range: [0.6, 0.9], using 0.8 as balanced default
    BUDGET_INERTIA_ALPHA = 0.8
    
    def __init__(self, profile):
        self.profile = profile

        # Persistent internal state
        self.state = PressureState()
        self.budget = BehaviorBudget(
            effort=1.0,
            risk=0.0,
            persistence=1.0,
            exploration=0.0,
        )

        self.appraisal = AppraisalEngine()
        self.governance = GovernanceEngine(profile)

        self.step_count = 0
        self.no_progress_steps = 0
        self.last_step_time = time.monotonic()

        # Terminal failure state
        self._halted = False
        self._failure = FailureType.NONE
        self._reason = None
        
        # Budget inertia: track previous budget for smoothing
        self._previous_budget = self.budget
        
        # Risk tracking: for freezing during RECOVERING
        self._previous_risk = 0.0
        
        # Stable budget snapshot: last non-RECOVERING, non-HALTED budget
        # Used to bound recovery (effort/persistence cannot exceed pre-failure levels)
        self._stable_budget = self.budget

    def step(
        self, 
        reward: float, 
        novelty: float, 
        urgency: float, 
        difficulty: float = 0.0,
        trust: float = 1.0,
        dt: float = 1.0
    ) -> EngineResult:
        """
        Execute one step of the emotional engine.
        
        Post-Failure Semantics:
        ----------------------
        If the engine is HALTED, this method returns immediately with:
        - Zeroed budget (0.0, 0.0, 0.0, 0.0)
        - halted=True
        - The failure type and reason that caused the halt
        - mode=Mode.HALTED
        
        No state evolution, pressure accumulation, governance, or recovery
        occurs after HALT. This is terminal for the session.
        
        Args:
            reward: Reward signal from the environment
            novelty: Novelty signal indicating new information
            urgency: Urgency signal indicating time pressure
            difficulty: Evidence of control loss [0, 1]
            trust: Credibility of inputs [0, 1]
            dt: Time delta for processing temporal effects
            
        Returns:
            EngineResult containing current state, budget, mode, and failure info
        """
        if self._halted:
            return EngineResult(
                state=self.state,
                budget=BehaviorBudget(0.0, 0.0, 0.0, 0.0),
                halted=True,
                failure=self._failure,
                reason=self._reason,
                mode=Mode.HALTED,
            )

        now = time.monotonic()
        dt = now - self.last_step_time
        self.last_step_time = now
        self.step_count += 1
        halted = False
        failure = FailureType.NONE
        reason = None
        
        # --------------------------------------------------
        # 1. Progress tracking (stagnation)
        #    BOUNDARY: Engine DETECTS stagnation.
        #    Governance RESPONDS to stagnation.
        #    Profiles TUNE the response.
        # --------------------------------------------------
        if reward <= 0.0:
            self.no_progress_steps += 1
        else:
            self.no_progress_steps = 0

        stagnating = self.no_progress_steps >= self.profile.stagnation_window

        # --------------------------------------------------
        # 2. Appraisal → Pressure accumulation
        # --------------------------------------------------
        delta = self.appraisal.compute(
            reward=reward,
            novelty=novelty,
            urgency=urgency,
            difficulty=difficulty,
        )
        self.state = self.state.integrate(delta)

        # --------------------------------------------------
        # 3. Governance → Raw behavior budget (stateless)
        # --------------------------------------------------
        raw_budget = self.governance.compute(
            state=self.state,
            stagnating=stagnating,
            dt=dt,
        )

        # --------------------------------------------------
        # 4. Budget Inertia (smoothing across steps)
        #    new_budget = α * previous + (1 - α) * raw
        #    This is control stability, NOT learning.
        # --------------------------------------------------
        alpha = self.BUDGET_INERTIA_ALPHA
        self.budget = BehaviorBudget(
            effort=alpha * self._previous_budget.effort + (1 - alpha) * raw_budget.effort,
            risk=alpha * self._previous_budget.risk + (1 - alpha) * raw_budget.risk,
            exploration=alpha * self._previous_budget.exploration + (1 - alpha) * raw_budget.exploration,
            persistence=alpha * self._previous_budget.persistence + (1 - alpha) * raw_budget.persistence,
        )

        # --------------------------------------------------
        # 5. Mode determination (BEFORE recovery)
        #    Mode is derived from current budget state.
        # --------------------------------------------------
        if self.budget.effort < 0.3 or self.budget.persistence < 0.3:
            mode = Mode.RECOVERING
        else:
            mode = Mode.IDLE

        # --------------------------------------------------
        # 6. Risk freezing during RECOVERING
        #    INVARIANT: Risk does NOT change during RECOVERING.
        #    This overrides BOTH governance output AND inertia.
        #    Prevents upward drift toward OVERRISK during recovery.
        # --------------------------------------------------
        if mode == Mode.RECOVERING:
            self.budget = BehaviorBudget(
                effort=self.budget.effort,
                risk=self._previous_risk,  # Freeze risk to previous value
                exploration=self.budget.exploration,
                persistence=self.budget.persistence,
            )

        # --------------------------------------------------
        # 7. Recovery (ONLY when mode == RECOVERING)
        #    INVARIANT: Recovery occurs ONLY in RECOVERING mode.
        #    INVARIANT: Recovered budget ≤ last stable (non-RECOVERING) budget.
        # --------------------------------------------------
        # Recovery semantics:
        # - Recovery occurs only in RECOVERING mode
        # - Recovery affects effort and persistence only
        # - Risk and exploration must never increase during recovery
        # - Recovery is bounded by pre-failure stable budget
        if mode == Mode.RECOVERING and dt >= self.profile.recovery_delay:
            self.budget = BehaviorBudget(
                effort=min(
                    self._stable_budget.effort,  # Bound by pre-failure level
                    self.profile.recovery_cap,
                    self.budget.effort + self.profile.recovery_rate * dt
                ),
                persistence=min(
                    self._stable_budget.persistence,  # Bound by pre-failure level
                    self.profile.recovery_cap,
                    self.budget.persistence + self.profile.recovery_rate * dt
                ),
                risk=self.budget.risk,  # Already frozen above
                exploration=self.budget.exploration,
            )

        # --------------------------------------------------
        # 8. Update tracking state for next step
        # --------------------------------------------------
        # Update previous budget for inertia (AFTER all modifications)
        self._previous_budget = self.budget
        
        # Update previous risk for freezing (use current budget's risk)
        self._previous_risk = self.budget.risk
        
        # Update stable budget snapshot ONLY when in IDLE (normal operation)
        if mode == Mode.IDLE:
            self._stable_budget = self.budget

        # --------------------------------------------------
        # 9. Failure checks (ordered, terminal)
        # --------------------------------------------------
        if self.budget.exploration >= self.profile.max_exploration:
            halted = True
            failure = FailureType.SAFETY
            reason = "exploration_exceeded"

        elif self.budget.risk >= self.profile.max_risk:
            halted = True
            failure = FailureType.OVERRISK
            reason = "risk_exceeded"

        elif self.budget.effort <= self.profile.exhaustion_threshold:
            halted = True
            failure = FailureType.EXHAUSTION
            reason = "exhaustion"

        elif stagnating and self.budget.effort <= self.profile.stagnation_effort_floor:
            halted = True
            failure = FailureType.STAGNATION
            reason = "stagnation"

        elif self.step_count >= self.profile.max_steps:
            # EXTERNAL failure semantics:
            # --------------------------
            # This is a SAFETY FUSE, not emotional regulation.
            # - It is NOT governance (not derived from pressure)
            # - It is NOT learned or adaptive
            # - It is a hard external limit to prevent runaway execution
            # - It is distinguishable from governance failures by FailureType.EXTERNAL
            halted = True
            failure = FailureType.EXTERNAL
            reason = "max_steps"

        # --------------------------------------------------
        # 10. Terminal state transition
        # --------------------------------------------------
        # Post-failure semantics:
        # - HALTED is terminal for the session
        # - State does not evolve after HALT
        # - Pressure does not accumulate
        # - Governance and recovery no longer apply
        # - Budget remains permanently zeroed
        if halted:
            self._halted = True
            self._failure = failure
            self._reason = reason
            mode = Mode.HALTED

        return EngineResult(
            state=self.state,
            budget=self.budget if not halted else BehaviorBudget(0.0, 0.0, 0.0, 0.0),
            halted=self._halted,
            failure=self._failure,
            reason=self._reason,
            mode=mode,
            pressure_log={
                "confidence": self.state.confidence,
                "frustration": self.state.frustration,
                "curiosity": self.state.curiosity,
                "arousal": self.state.arousal,
                "risk": self.state.risk,
                "trust": trust,  # First-class observability
            },
        )

    # Minimum steps before reset is allowed (anti-spam)
    RESET_COOLDOWN_STEPS = 5
    
    def reset(self, reason: str) -> None:
        """
        Manually reset the engine from a HALTED state.
        
        This is the ONLY way to recover from a halt. It should be used
        sparingly, typically after human intervention or a major context switch.
        
        Anti-Abuse: Reset requires at least RESET_COOLDOWN_STEPS steps to have
        occurred (unless the engine is halted, in which case reset is always allowed).
        
        Args:
            reason: Explanation for why the reset is occurring (audit trail).
            
        Raises:
            RuntimeError: If reset is called before cooldown period.
        """
        # Anti-spam: Require minimum steps before reset (unless halted)
        if not self._halted and self.step_count < self.RESET_COOLDOWN_STEPS:
            raise RuntimeError(
                f"Reset blocked: Only {self.step_count} steps elapsed. "
                f"Minimum {self.RESET_COOLDOWN_STEPS} required (or engine must be halted)."
            )
            
        self._halted = False
        self._failure = FailureType.NONE
        self._reason = None
        
        # Reset step count for cooldown tracking
        self.step_count = 0
        
        # Reset budget to IDLE state (full capacity)
        self.budget = BehaviorBudget(
            effort=1.0,
            risk=0.0,
            persistence=1.0,
            exploration=0.0
        )
        self._previous_budget = self.budget
        self._stable_budget = self.budget
        
        # We generally do NOT reset accumulated pressure state (self.state)
        # because the emotional context should persist. The 'reset' gives
        # the agent a fresh budget to DEAL with that pressure, not a lobotomy.
