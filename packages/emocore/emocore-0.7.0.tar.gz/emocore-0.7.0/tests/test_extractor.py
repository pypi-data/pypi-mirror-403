import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from emocore.observation import Observation
from emocore.extractor import RuleBasedExtractor
from emocore.signals import Signals

class TestRuleBasedExtractor:
    
    @pytest.fixture
    def extractor(self):
        return RuleBasedExtractor()
        
    def test_reward_mechanics(self, extractor):
        """Test R-1: Reward behavior on success, failure, and stagnation."""
        # 1. Success increases reward
        obs_success = Observation(
            action="test", result="success", 
            env_state_delta=0.2, agent_state_delta=0.1, elapsed_time=1.0
        )
        s1 = extractor.extract(obs_success)
        assert s1.reward > 0
        
        # 2. Failure decreases reward
        obs_fail = Observation(
            action="test", result="failure", 
            env_state_delta=0.0, agent_state_delta=0.1, elapsed_time=1.0
        )
        s2 = extractor.extract(obs_fail)
        assert s2.reward < s1.reward
        
        # 3. Stagnation (low delta) decays reward
        # Reset extractor to clear state
        extractor.reset()
        extractor.current_reward = 0.5
        
        obs_stagnant = Observation(
            action="spin", result="success", 
            env_state_delta=0.01, agent_state_delta=0.01, elapsed_time=1.0
        )
        s3 = extractor.extract(obs_stagnant)
        assert s3.reward < 0.5  # Decay applied
        
    def test_novelty_mechanics(self, extractor):
        """Test novelty decay on repetition and debt accumulation."""
        obs = Observation(
            action="cmd_A", result="success", 
            env_state_delta=0.2, agent_state_delta=0.1, elapsed_time=1.0
        )
        
        # First time: High novelty
        s1 = extractor.extract(obs)
        assert s1.novelty > 0.5
        
        # Repetition: Lower novelty
        s2 = extractor.extract(obs)
        assert s2.novelty < s1.novelty
        
    def test_novelty_debt(self, extractor):
        """Test N-5: Novelty debt suppression (Exploration Theater)."""
        extractor.current_reward = -0.5  # Negative reward context
        extractor.novelty_debt = 6.0     # High debt (> 5.0 threshold)
        
        obs = Observation(
            action="new_cmd", result="failure", 
            env_state_delta=0.2, agent_state_delta=0.1, elapsed_time=1.0
        )
        
        signals = extractor.extract(obs)
        assert signals.novelty == 0.0  # Forced suppression
        
    def test_signal_trust_decay(self, extractor):
        """Test trust decay on inconsistencies."""
        # Case: Success but no state change (Fake success)
        obs_fake = Observation(
            action="faker", result="success", 
            env_state_delta=0.0, agent_state_delta=0.0, elapsed_time=1.0
        )
        
        extractor.signal_trust = 1.0
        extractor.extract(obs_fake)
        assert extractor.signal_trust < 1.0
        
    def test_difficulty_dominance(self, extractor):
        """Test D-1: Difficulty suppresses novelty."""
        obs = Observation(
            action="cmd_B", result="failure", 
            env_state_delta=0.0, agent_state_delta=0.0, elapsed_time=1.0
        )
        
        # Manually pump difficulty
        extractor.current_difficulty = 0.9
        
        signals = extractor.extract(obs)
        
        # Novelty should be heavily suppressed by (1 - 0.9^2) ≈ 0.19 factor
        # Expected raw novelty ~1.0
        assert signals.novelty < 0.4
        assert signals.difficulty > 0.8

    def test_stagnation_frustration_spike(self, extractor):
        """Test frustration spike after STAGNATION_STEPS."""
        obs = Observation(
            action="stagnate", result="success", 
            env_state_delta=0.0, agent_state_delta=0.0, elapsed_time=1.0
        )
        
        # Run for N-1 steps
        for _ in range(extractor.stagnation_limit - 1):
             extractor.extract(obs)
        
        diff_pre = extractor.current_difficulty
        
        # The Nth step should trigger spike
        signals = extractor.extract(obs)
        assert signals.difficulty > diff_pre + 0.3  # Significant jump

    def test_state_cycling_detection(self, extractor):
        """Test S-1: State cycling detection prevents file churn gaming."""
        # First observation - new state
        obs1 = Observation(
            action="write_file", result="success", 
            env_state_delta=0.5, agent_state_delta=0.1, elapsed_time=1.0
        )
        s1 = extractor.extract(obs1)
        assert s1.reward > 0  # Should get credit for first time
        
        # Different observation - also new
        obs2 = Observation(
            action="read_file", result="success", 
            env_state_delta=0.3, agent_state_delta=0.1, elapsed_time=2.0
        )
        s2 = extractor.extract(obs2)
        
        # Now cycle back to the same state as obs1 (file churn)
        obs3 = Observation(
            action="write_file", result="success", 
            env_state_delta=0.5, agent_state_delta=0.1, elapsed_time=3.0
        )
        s3 = extractor.extract(obs3)
        
        # S-1: env_state_delta should be treated as 0 because state hash repeats
        # Reward still increases slightly from agent_delta, but much less than if
        # env_state_delta counted. The key invariant: cycling doesn't give full credit.
        # Since s2 gave full credit (different state), s3 should give less boost.
        reward_boost_s2 = s2.reward - s1.reward  # Full credit boost
        reward_boost_s3 = s3.reward - s2.reward  # Cycling boost (should be less)
        
        # The cycling step should give less reward boost than a genuine new state
        assert reward_boost_s3 < reward_boost_s2


    def test_llm_extractor_tokens(self):
        """Test token budget urgency in LLMAgentExtractor."""
        from emocore.extractor import LLMAgentExtractor
        extractor = LLMAgentExtractor(token_limit=1000)
        
        obs = Observation(
            action="gen", result="success", 
            env_state_delta=0.0, agent_state_delta=0.1, 
            elapsed_time=1.0, tokens_used=500
        )
        
        s1 = extractor.extract(obs)
        assert s1.urgency >= 0.5  # 500/1000 tokens used
        
        # Next step pushes it to limit
        s2 = extractor.extract(obs)
        assert s2.urgency == 1.0


    def test_llm_extractor_reasoning_trust(self):
        """Test reasoning theater trust decay."""
        from emocore.extractor import LLMAgentExtractor
        extractor = LLMAgentExtractor()
        
        # High reasoning, zero env delta
        obs = Observation(
            action="think", result="success", 
            env_state_delta=0.0, agent_state_delta=0.9, 
            elapsed_time=1.0
        )
        
        t1 = extractor.signal_trust
        extractor.extract(obs)
        t2 = extractor.signal_trust
        
        # Should decay faster than normal trust decay
        assert t2 <= t1 * 0.9


    def test_tool_extractor_bonus(self):
        """Test tangible environment change bonus in ToolAgentExtractor."""
        from emocore.extractor import ToolAgentExtractor
        extractor = ToolAgentExtractor()
        
        obs = Observation(
            action="write", result="success", 
            env_state_delta=0.5, agent_state_delta=0.1, 
            elapsed_time=1.0
        )
        
        s1 = extractor.extract(obs)
        # Normal success boost is +0.3. Bonus is +0.2. Total +0.5.
        assert s1.reward >= 0.5
