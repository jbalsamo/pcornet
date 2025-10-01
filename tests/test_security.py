"""
Tests for the security module.
"""
import pytest
import time
from modules.security import InputValidator, RateLimiter, InputValidationException, RateLimitException

class TestInputValidator:
    """Tests for InputValidator."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = InputValidator(max_length=5000)
        assert validator.max_length == 5000
    
    def test_valid_input(self):
        """Test validation of valid input."""
        validator = InputValidator()
        result = validator.validate_input("Hello, how are you?")
        
        assert result["valid"] == True
        assert result["length"] == 19
    
    def test_empty_input(self):
        """Test validation of empty input."""
        validator = InputValidator()
        result = validator.validate_input("")
        
        assert result["valid"] == False
        assert "empty" in result["error"].lower()
    
    def test_input_too_long(self):
        """Test validation of input exceeding max length."""
        validator = InputValidator(max_length=10)
        result = validator.validate_input("This is a very long input string")
        
        assert result["valid"] == False
        assert "exceeds maximum length" in result["error"]
    
    def test_dangerous_script_tag(self):
        """Test detection of script tags."""
        validator = InputValidator()
        result = validator.validate_input("<script>alert('xss')</script>")
        
        assert result["valid"] == False
        assert "unsafe" in result["error"].lower()
    
    def test_javascript_protocol(self):
        """Test detection of javascript: protocol."""
        validator = InputValidator()
        result = validator.validate_input("javascript:alert('xss')")
        
        assert result["valid"] == False
        assert "unsafe" in result["error"].lower()
    
    def test_excessive_special_characters(self):
        """Test detection of excessive special characters."""
        validator = InputValidator()
        result = validator.validate_input("!@#$%^&*()!@#$%^&*()")
        
        assert result["valid"] == False
        assert "special characters" in result["error"].lower()
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        validator = InputValidator()
        
        # Remove HTML tags
        sanitized = validator.sanitize_input("<p>Hello <b>world</b></p>")
        assert "<p>" not in sanitized
        assert "<b>" not in sanitized
        assert "Hello world" in sanitized
        
        # Normalize whitespace
        sanitized = validator.sanitize_input("Hello    world")
        assert sanitized == "Hello world"

class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_calls=5, time_window=30)
        assert limiter.max_calls == 5
        assert limiter.time_window == 30
    
    def test_allow_within_limit(self):
        """Test requests within rate limit are allowed."""
        limiter = RateLimiter(max_calls=3, time_window=60)
        
        # First request should be allowed
        result1 = limiter.check_rate_limit("session1")
        assert result1["allowed"] == True
        assert result1["remaining"] == 2
        
        # Second request should be allowed
        result2 = limiter.check_rate_limit("session1")
        assert result2["allowed"] == True
        assert result2["remaining"] == 1
    
    def test_block_when_limit_exceeded(self):
        """Test requests are blocked when limit is exceeded."""
        limiter = RateLimiter(max_calls=2, time_window=60)
        
        # Use up the limit
        limiter.check_rate_limit("session1")
        limiter.check_rate_limit("session1")
        
        # Third request should be blocked
        result = limiter.check_rate_limit("session1")
        assert result["allowed"] == False
        assert "retry_after" in result
    
    def test_separate_sessions(self):
        """Test that different sessions have separate rate limits."""
        limiter = RateLimiter(max_calls=2, time_window=60)
        
        # Use up limit for session1
        limiter.check_rate_limit("session1")
        limiter.check_rate_limit("session1")
        
        # session2 should still be allowed
        result = limiter.check_rate_limit("session2")
        assert result["allowed"] == True
    
    def test_reset_session(self):
        """Test resetting a session's rate limit."""
        limiter = RateLimiter(max_calls=2, time_window=60)
        
        # Use up the limit
        limiter.check_rate_limit("session1")
        limiter.check_rate_limit("session1")
        
        # Reset the session
        limiter.reset_session("session1")
        
        # Should be allowed again
        result = limiter.check_rate_limit("session1")
        assert result["allowed"] == True
    
    def test_get_stats(self):
        """Test getting rate limit statistics."""
        limiter = RateLimiter(max_calls=5, time_window=60)
        
        limiter.check_rate_limit("session1")
        limiter.check_rate_limit("session1")
        
        stats = limiter.get_stats("session1")
        assert stats["session_id"] == "session1"
        assert stats["requests_in_window"] == 2
        assert stats["max_calls"] == 5
        assert stats["remaining"] == 3
    
    def test_time_window_expiry(self):
        """Test that old requests expire after time window."""
        limiter = RateLimiter(max_calls=2, time_window=1)  # 1 second window
        
        # Make requests
        limiter.check_rate_limit("session1")
        limiter.check_rate_limit("session1")
        
        # Should be blocked
        result = limiter.check_rate_limit("session1")
        assert result["allowed"] == False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        result = limiter.check_rate_limit("session1")
        assert result["allowed"] == True
