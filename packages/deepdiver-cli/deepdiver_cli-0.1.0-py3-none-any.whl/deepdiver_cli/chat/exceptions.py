"""
Exception classes for chat provider operations.

This module defines a hierarchy of exceptions for handling errors
in chat provider operations, including request/response processing,
configuration errors, and provider-specific issues.
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base exception for all provider-related errors."""

    def __init__(self, message: str, provider_name: str | None = None):
        self.message = message
        self.provider_name = provider_name
        super().__init__(message)

    def __str__(self) -> str:
        if self.provider_name:
            return f"[{self.provider_name}] {self.message}"
        return self.message


class ConfigurationError(ProviderError):
    """Configuration-related errors."""

    def __init__(self, message: str, provider_name: str | None = None, config_key: str | None = None):
        self.config_key = config_key
        super().__init__(message, provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.config_key:
            return f"{base} (config: {self.config_key})"
        return base


class AuthenticationError(ProviderError):
    """Authentication errors (invalid API keys, etc.)."""

    def __init__(self, message: str, provider_name: str | None = None):
        super().__init__(f"Authentication failed: {message}", provider_name)


class RateLimitError(ProviderError):
    """Rate limit errors."""

    def __init__(self, message: str, provider_name: str | None = None, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {message}", provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after}s)"
        return base


class TimeoutError(ProviderError):
    """Timeout errors."""

    def __init__(self, message: str, provider_name: str | None = None, timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Timeout: {message}", provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.timeout_seconds:
            return f"{base} (timeout: {self.timeout_seconds}s)"
        return base


class NetworkError(ProviderError):
    """Network-related errors (connection issues, etc.)."""

    def __init__(self, message: str, provider_name: str | None = None, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(f"Network error: {message}", provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.status_code:
            return f"{base} (status: {self.status_code})"
        return base


class ParseError(ProviderError):
    """Response parsing errors."""

    def __init__(self, message: str, provider_name: str | None = None, raw_data: str | None = None):
        self.raw_data = raw_data
        super().__init__(f"Parse error: {message}", provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.raw_data:
            return f"{base} (data: {self.raw_data[:100]}...)"
        return base


class StreamError(ProviderError):
    """Stream processing errors."""

    def __init__(self, message: str, provider_name: str | None = None, chunk_index: int | None = None):
        self.chunk_index = chunk_index
        super().__init__(f"Stream error: {message}", provider_name)

    def __str__(self) -> str:
        base = super().__str__()
        if self.chunk_index is not None:
            return f"{base} (chunk: {self.chunk_index})"
        return base


class UnsupportedFeatureError(ProviderError):
    """Errors for unsupported features."""

    def __init__(self, feature: str, provider_name: str | None = None):
        self.feature = feature
        super().__init__(f"Unsupported feature: {feature}", provider_name)


class RetryableError(ProviderError):
    """
    Base class for errors that should trigger retry.

    Subclasses of this error will be caught by retry mechanisms
    and the operation will be retried according to the retry policy.
    """

    def __init__(self, message: str, provider_name: str | None = None, max_retries: int = 3):
        self.max_retries = max_retries
        super().__init__(f"Retryable error: {message}", provider_name)


# Common retryable error types (for convenience)
class RetryableTimeoutError(TimeoutError, RetryableError):
    """Timeout error that should trigger retry."""
    pass


class RetryableNetworkError(NetworkError, RetryableError):
    """Network error that should trigger retry."""
    pass


class RetryableRateLimitError(RateLimitError, RetryableError):
    """Rate limit error that should trigger retry."""
    pass


# Utility functions
def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    return isinstance(error, RetryableError)


def get_provider_name_from_error(error: Exception) -> str | None:
    """Extract provider name from an error if available."""
    if isinstance(error, ProviderError):
        return error.provider_name
    return None


def wrap_exception(error: Exception, provider_name: str | None = None) -> ProviderError:
    """
    Wrap a generic exception into a ProviderError.

    Useful for converting third-party library exceptions into
    our own exception hierarchy.
    """
    if isinstance(error, ProviderError):
        return error

    # Map common exception types to our hierarchy
    import asyncio
    import httpx
    import openai

    if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        return TimeoutError(str(error), provider_name)
    elif isinstance(error, (openai.RateLimitError,)):
        return RateLimitError(str(error), provider_name)
    elif isinstance(error, (openai.AuthenticationError,)):
        return AuthenticationError(str(error), provider_name)
    elif isinstance(error, (httpx.TimeoutException,)):
        return TimeoutError(str(error), provider_name)
    elif isinstance(error, (httpx.NetworkError, ConnectionError)):
        return NetworkError(str(error), provider_name)
    elif isinstance(error, (openai.APIError, httpx.HTTPStatusError)):
        return NetworkError(str(error), provider_name, getattr(error, 'status_code', None))
    else:
        return ProviderError(str(error), provider_name)