"""SendBaba SDK Exceptions"""

class SendBabaError(Exception):
    """Base exception for SendBaba SDK"""
    pass

class AuthenticationError(SendBabaError):
    """Authentication failed"""
    pass

class RateLimitError(SendBabaError):
    """Rate limit exceeded"""
    pass

class ValidationError(SendBabaError):
    """Validation error"""
    pass

class NotFoundError(SendBabaError):
    """Resource not found"""
    pass
