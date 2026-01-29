# emocore/governance.py
"""
GovernanceEngine: Translates pressure state into behavioral permission.

What GovernanceEngine does:
- Converts PressureState into BehaviorBudget via matrix multiplication
- Applies profile-based scaling and decay
- Responds to stagnation signals from Engine
- Clips output to [0, 1] range

What GovernanceEngine does NOT do:
- Detect stagnation (that's Engine's job)
- Decide when to halt (that's Engine's job)
- Learn or optimize (matrices are fixed)
- Control actions (that's downstream control primitives)

Assumptions:
- PressureState has exactly 5 canonical axes in order: confidence, frustration, curiosity, arousal, risk
- BehaviorBudget has exactly 4 dimensions: effort, risk, exploration, persistence
- W and V matrices are fixed for the prototype
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from dataclasses import dataclass
from typing import Optional
from emocore.behavior import BehaviorBudget
from emocore.state import PressureState


class GovernanceEngine:
    """
    Stateless governance engine that computes behavioral permission from pressure.
    
    The governance equation is:
        g = W.T @ s - V.T @ s
    
    Where:
    - s is the pressure state vector [confidence, frustration, curiosity, arousal, risk]
    - W is the enabling matrix (positive pressure → positive budget)
    - V is the suppressive matrix (frustration suppresses all dimensions)
    - g is the raw governance output [effort, risk, exploration, persistence]
    
    This is NOT learning. The matrices are fixed.
    This is NOT optimization. The computation is deterministic.
    This is pure governance: pressure → permission.
    
    Boundary clarification:
    - Engine DETECTS stagnation and passes flag to governance
    - Governance RESPONDS to stagnation by scaling effort/persistence
    - Profiles TUNE the response via scaling and decay parameters
    """
    
    # Enabling matrix (pressures → governance)
    # Rows: pressure axes (confidence, frustration, curiosity, arousal, risk)
    # Cols: budget dimensions (effort, risk, exploration, persistence)
    W = np.array([
        [0.6, 0.3, 0.2, 0.5],  # confidence
        [0.0, 0.0, 0.0, 0.0],  # frustration (no enabling)
        [0.2, 0.1, 0.7, 0.1],  # curiosity
        [0.3, 0.2, 0.1, 0.2],  # arousal
        [0.1, 0.5, 0.3, 0.1],  # risk
    ])

    # Suppressive matrix (only frustration suppresses)
    # Frustration suppresses all budget dimensions
    V = np.array([
        [0.0, 0.0, 0.0, 0.0],  # confidence
        [0.7, 0.9, 0.9, 0.8],  # frustration suppresses all
        [0.0, 0.0, 0.0, 0.0],  # curiosity
        [0.0, 0.0, 0.0, 0.0],  # arousal
        [0.0, 0.0, 0.0, 0.0],  # risk
    ])

    def __init__(self, profile=None):
        self.profile = profile

    def compute(self, state: PressureState, stagnating: bool = False, dt: float = 0.0) -> BehaviorBudget:
        s = np.array([
            state.confidence,
            state.frustration,
            state.curiosity,
            state.arousal,
            state.risk,
        ])

        g = self.W.T @ s - self.V.T @ s

        # 1. Stagnation Scaling (Before Profile Scaling? Or After? 
        # User said: "Stagnation is engine policy... applies to BehaviorBudget".
        # But now "Governance scales...". 
        # Usually suppression happens early or late.
        # Let's apply it to the raw matrix output 'g' for consistency, 
        # OR apply it to the final budget values.
        # The previous Engine implementation applied it to the BehaviorBudget logic.
        # Let's do it on 'g' to keep matrix operations together, or keep it explicit?
        # User said: "Stagnation handling... Governance starts reacting to stagnating".
        # Let's apply it to 'g' indices corresponding to Effort(0) and Persistence(3).
        if stagnating and self.profile:
            g[0] *= self.profile.stagnation_effort_scale
            g[3] *= self.profile.stagnation_persistence_scale

        # 2. Profile Scaling
        if self.profile:
            g[0] *= self.profile.effort_scale
            g[1] *= self.profile.risk_scale
            g[2] *= self.profile.exploration_scale
            g[3] *= self.profile.persistence_scale

        # 3. Decay (Time + Step)
        # Decay is subtracted. 
        # Previous engine logic: max(0, val - decay - dt*time_decay)
        # We apply this to `g`.
        if self.profile:
            decay_expl = self.profile.exploration_decay + dt * self.profile.time_exploration_decay
            decay_pers = self.profile.persistence_decay + dt * self.profile.time_persistence_decay
            
            g[2] -= decay_expl
            g[3] -= decay_pers

        # 4. Clip
        g = np.clip(g, 0.0, 1.0)

        return BehaviorBudget(
            effort=float(g[0]),
            risk=float(g[1]),
            exploration=float(g[2]),
            persistence=float(g[3]),
        )
