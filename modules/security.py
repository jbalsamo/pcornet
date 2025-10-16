"""
Provides security-related utilities for input validation and rate limiting.

This module contains the `InputValidator` class for sanitizing and validating
user input to prevent common security risks like XSS, and the `RateLimiter`
class to protect the application from abuse by limiting the number of requests
from a single session within a given time window.

Custom exceptions `InputValidationException` and `RateLimitException` are also
defined for handling specific error conditions.
"""
import re
import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InputValidationException(Exception):
    """Exception raised for errors during input validation."""
    pass

class RateLimitException(Exception):
    """Exception raised when a user exceeds the defined rate limit."""
    pass

class InputValidator:
    """
    A class for validating and sanitizing user-provided input strings.

    This validator checks for common security issues such as excessive length,
    empty input, dangerous patterns (e.g., script tags), and an unusual ratio
    of special characters.
    """
    
    def __init__(self, max_length: int = 10000):
        """
        Initializes the InputValidator.

        Args:
            max_length (int): The maximum allowed length for an input string.
                              Defaults to 10000.
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
        """
        Validates a user input string against a set of security rules.

        Args:
            user_input (str): The string to validate.

        Returns:
            Dict[str, Any]: A dictionary containing a 'valid' boolean and an
                            'error' message if validation fails.
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
        """
        Sanitizes a user input string by removing potentially harmful content.

        This method removes HTML-like tags, null bytes, and normalizes
        whitespace to produce a safer version of the input string.

        Args:
            user_input (str): The string to sanitize.

        Returns:
            str: The sanitized string.
        """
        # Remove any HTML/script tags
        sanitized = re.sub(r'<[^>]*>', '', user_input)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized

class RateLimiter:
    """
    A simple in-memory rate limiter based on a sliding time window.

    This class tracks the timestamps of requests for different session IDs
    to enforce a limit on the number of calls allowed within a specified
    time period.
    """
    
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """
        Initializes the RateLimiter.

        Args:
            max_calls (int): The maximum number of calls allowed within the
                             time window. Defaults to 10.
            time_window (int): The duration of the time window in seconds.
                               Defaults to 60.
        """
        self.max_calls = max_calls
        self.time_window = time_window
        
        # Track requests per session
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        logger.info(f"RateLimiter initialized: {max_calls} calls per {time_window} seconds")
    
    def check_rate_limit(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Checks if a request from a given session is within the rate limit.

        If the request is allowed, it is recorded. If it is denied, information
        about when to retry is provided.

        Args:
            session_id (str): A unique identifier for the user or session.

        Returns:
            Dict[str, Any]: A dictionary indicating if the request is 'allowed',
                            and if not, a 'retry_after' value in seconds.
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
        """
        Resets the rate limit count for a specific session.

        Args:
            session_id (str): The identifier for the session to reset.
        """
        if session_id in self.requests:
            del self.requests[session_id]
            logger.info(f"Rate limit reset for session {session_id}")
    
    def get_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Retrieves the current rate limit statistics for a session.

        Args:
            session_id (str): The identifier for the session.

        Returns:
            Dict[str, Any]: A dictionary with details about the session's
                            current request count and remaining allowance.
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
