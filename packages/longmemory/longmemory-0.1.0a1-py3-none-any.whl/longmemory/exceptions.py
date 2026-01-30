class LongMemoryError(Exception):
    """Base exception for all LongMemory errors."""
    pass

class AuthenticationError(LongMemoryError):
    """Raised when API keys are invalid."""
    pass

class InvalidRequestError(LongMemoryError):
    """Raised when parameters (like missing user_id) are wrong."""
    pass

class ServerError(LongMemoryError):
    """Raised when LongMemory.io is down."""
    pass