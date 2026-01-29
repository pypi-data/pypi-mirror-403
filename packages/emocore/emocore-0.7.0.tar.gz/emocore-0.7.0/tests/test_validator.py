import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from emocore.validator import SignalValidator, ValidationError
from emocore.signals import Signals

class TestSignalValidator:
    
    @pytest.fixture
    def validator(self):
        return SignalValidator(strict=False)
        
    def test_range_clamping(self, validator):
        """Test that values outside standard ranges are clamped."""
        # Reward [-1, 1], others [0, 1]
        invalid = Signals(
            reward=1.5,      # Should be 1.0
            novelty=-0.2,    # Should be 0.0
            urgency=100.0,   # Should be 1.0
            difficulty=-0.5  # Should be 0.0
        )
        
        valid = validator.validate(invalid)
        
        assert valid.reward == 1.0
        assert valid.novelty == 0.0
        assert valid.urgency == 1.0
        assert valid.difficulty == 0.0
        
    def test_smoothness_limiting(self, validator):
        """Test max delta of 0.5 per step."""
        # Step 1: Base
        s1 = Signals(reward=0.0, novelty=0.0)
        validator.validate(s1)
        
        # Step 2: Sudden jump 1.0
        s2 = Signals(reward=1.0, novelty=0.0)
        valid = validator.validate(s2)
        
        # Reward should be capped at 0.0 + 0.5 = 0.5
        assert valid.reward == 0.5
        
    def test_strict_mode(self):
        """Test that strict=True raises exceptions."""
        strict_val = SignalValidator(strict=True)
        
        invalid = Signals(reward=2.0)
        
        with pytest.raises(ValidationError) as excinfo:
            strict_val.validate(invalid)
        
        assert "Range violations" in str(excinfo.value)
        
    def test_oscillation_detection(self, validator):
        """Test detection of rapid sign flips in strict mode."""
        strict_val = SignalValidator(strict=True)
        
        # History of flips: + - + - (4th flip triggers)
        # Use small amplitude to pass smoothness check (limit 0.5)
        seq = [0.2, -0.2, 0.2, -0.2, 0.2]
        
        for k, val in enumerate(seq):
            s = Signals(reward=val)
            if k == 4:
                with pytest.raises(ValidationError):
                    strict_val.validate(s)
            else:
                strict_val.validate(s)
