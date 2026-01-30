"""Session related exceptions."""


class SessionError(Exception):
    """Base exception for session related errors."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""
    pass


class SessionValidationError(SessionError):
    """Raised when session data validation fails."""
    pass


class SessionStorageError(SessionError):
    """Raised when session storage operations fail."""
    pass


class SessionConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    pass