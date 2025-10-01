"""
Security module for input validation and rate limiting.
"""
import re
import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InputValidationException(Exception):
    """Exception raised when input validation fails."""
    pass

class RateLimitException(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class InputValidator:
    """Validates and sanitizes user input."""
    
    def __init__(self, max_length: int = 10000):
        """Initialize input validator.
        
        Args:
            max_length: Maximum allowed input length
        """
        self.max_length = max_length
        
        # Patterns to detect potentially harmful input
        self.dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript protocol
            r'on\w+\s*=',                # Event handlers
            r'eval\s*\(',                # eval calls
            r'exec\s*\(',                # exec calls
        ]
        
        logger.info(f"InputValidator initialized with max_length={max_length}")
    
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input.
        
        Args:
            user_input: The user's input to validate
            
        Returns:
            Dictionary with validation results
        """
        # Check if input is empty
        if not user_input or not user_input.strip():
            return {
                "valid": False,
                "error": "Input cannot be empty"
            }
        
        # Check length
        if len(user_input) > self.max_length:
            return {
                "valid": False,
                "error": f"Input exceeds maximum length of {self.max_length} characters"
            }
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                return {
                    "valid": False,
                    "error": "Input contains potentially unsafe content"
                }
        
        # Check for excessive special characters (potential injection attempts)
        special_char_count = sum(1 for c in user_input if not c.isalnum() and not c.isspace())
        if special_char_count > len(user_input) * 0.5:
            logger.warning(f"Excessive special characters detected: {special_char_count}/{len(user_input)}")
            return {
                "valid": False,
                "error": "Input contains excessive special characters"
            }
        
        return {
            "valid": True,
            "length": len(user_input),
            "sanitized": True
        }
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input by removing potentially harmful content.
        
        Args:
            user_input: The user's input to sanitize
            
        Returns:
            Sanitized input string
        """
        # Remove any HTML/script tags
        sanitized = re.sub(r'<[^>]*>', '', user_input)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized

class RateLimiter:
    """Rate limiter to prevent abuse."""
    
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        
        # Track requests per session
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        logger.info(f"RateLimiter initialized: {max_calls} calls per {time_window} seconds")
    
    def check_rate_limit(self, session_id: str = "default") -> Dict[str, Any]:
        """Check if a request should be allowed based on rate limits.
        
        Args:
            session_id: Identifier for the session/user
            
        Returns:
            Dictionary with rate limit status
        """
        current_time = time.time()
        
        # Get request history for this session
        request_times = self.requests[session_id]
        
        # Remove old requests outside the time window
        cutoff_time = current_time - self.time_window
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= self.max_calls:
            oldest_request = request_times[0]
            retry_after = int(oldest_request + self.time_window - current_time)
            
            logger.warning(f"Rate limit exceeded for session {session_id}")
            return {
                "allowed": False,
                "retry_after": retry_after,
                "requests_made": len(request_times),
                "max_calls": self.max_calls
            }
        
        # Add current request
        request_times.append(current_time)
        
        return {
            "allowed": True,
            "requests_made": len(request_times),
            "max_calls": self.max_calls,
            "remaining": self.max_calls - len(request_times)
        }
    
    def reset_session(self, session_id: str = "default") -> None:
        """Reset rate limit for a session.
        
        Args:
            session_id: Identifier for the session to reset
        """
        if session_id in self.requests:
            del self.requests[session_id]
            logger.info(f"Rate limit reset for session {session_id}")
    
    def get_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """Get rate limit statistics for a session.
        
        Args:
            session_id: Identifier for the session
            
        Returns:
            Dictionary with rate limit stats
        """
        request_times = self.requests.get(session_id, deque())
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        # Count recent requests
        recent_requests = sum(1 for t in request_times if t >= cutoff_time)
        
        return {
            "session_id": session_id,
            "requests_in_window": recent_requests,
            "max_calls": self.max_calls,
            "time_window": self.time_window,
            "remaining": max(0, self.max_calls - recent_requests)
        }
