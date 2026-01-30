"""
Base provider implementation with common functionality.

This module provides BaseProvider, which implements common functionality
for all chat providers, including:
- Automatic retry with exponential backoff
- Timeout handling
- Error handling and conversion to ErrorResponse
- Logging and telemetry
- Request/response transformation via RequestBuilder/ResponseParser

Concrete providers should inherit from BaseProvider and implement
the `_create_stream` method.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Dict, Tuple, Type

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..chat.chat_provider import ChatProvider
from ..chat.chat_model import LLMRequest, LLMProviderConfig
from ..chat.response_types import LLMResponse, ErrorResponse
from ..chat.transformer import RequestBuilder, ResponseParser
from ..chat.exceptions import (
    ProviderError,
    TimeoutError,
    is_retryable_error,
    wrap_exception,
)

logger = structlog.get_logger(__name__)


class BaseProvider(ChatProvider):
    """
    Base implementation for all chat providers.

    This class provides common functionality that all providers need,
    including retry logic, timeout handling, and error conversion.
    Concrete providers should:
    1. Inherit from BaseProvider
    2. Set `retryable_exceptions` class attribute
    3. Implement `_create_stream` method
    4. Provide RequestBuilder and ResponseParser instances
    """

    # Tuple of exception types that should trigger retry
    # Subclasses should override this with provider-specific exceptions
    retryable_exceptions: Tuple[Type[Exception], ...] = ()

    def __init__(
        self,
        provider_config: LLMProviderConfig,
        request_builder: RequestBuilder,
        response_parser: ResponseParser,
    ):
        """
        Initialize base provider.

        Args:
            provider_config: Provider configuration
            request_builder: Request builder for this provider
            response_parser: Response parser for this provider
        """
        super().__init__(provider_config)
        self.request_builder = request_builder
        self.response_parser = response_parser
        self._client = None  # Can be initialized by subclasses

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception_type(retryable_exceptions),
    )
    async def generate(self, request: LLMRequest) -> AsyncIterator[LLMResponse]:
        """
        Generate LLM response with automatic retry and error handling.

        This is the main entry point that handles:
        1. Request transformation via RequestBuilder
        2. Stream creation with timeout
        3. Response parsing via ResponseParser
        4. Automatic retry for retryable errors
        5. Error conversion to ErrorResponse

        Args:
            request: LLM request

        Yields:
            LLMResponse: Stream of response objects (deltas and complete types)

        Raises:
            ProviderError: For provider-specific errors after retries exhausted
            TimeoutError: If request times out
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"

        logger.debug(
            "provider.request.start",
            request_id=request_id,
            provider=self.provider_config.provider_name,
            model=request.model,
            has_tools=bool(request.tools),
            enable_thinking=request.enable_thinking,
        )

        try:
            # Build provider-specific request
            provider_request = self.request_builder.build_request(request)

            # Create stream with timeout
            stream = await self._create_stream_with_timeout(
                provider_request, request.timeout, request_id
            )

            # Parse and yield responses
            async for response in self.response_parser.parse_stream(stream, request):
                # Log certain response types for debugging
                self._log_response(response, request_id)

                yield response

                # If we get an error response, raise exception
                if isinstance(response, ErrorResponse) and not response.recoverable:
                    raise ProviderError(
                        f"{response.error_type}: {response.error_message}",
                        provider_name=self.provider_config.provider_name,
                    )

            logger.debug(
                "provider.request.success",
                request_id=request_id,
                elapsed=time.time() - start_time,
            )

        except asyncio.TimeoutError as exc:
            elapsed = time.time() - start_time
            logger.error(
                "provider.request.timeout",
                request_id=request_id,
                elapsed=elapsed,
                timeout=request.timeout,
            )
            yield ErrorResponse(
                error_type="TimeoutError",
                error_message=f"Request timed out after {elapsed:.2f}s (timeout: {request.timeout}s)",
                recoverable=True,
            )
            raise TimeoutError(
                f"Request timed out after {elapsed:.2f}s",
                provider_name=self.provider_config.provider_name,
                timeout_seconds=request.timeout,
            ) from exc

        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(
                "provider.request.error",
                request_id=request_id,
                error=str(exc),
                error_type=type(exc).__name__,
                elapsed=elapsed,
                exc_info=True,
            )

            # Convert to ProviderError if needed
            provider_error = wrap_exception(exc, self.provider_config.provider_name)

            # Yield error response
            yield ErrorResponse(
                error_type=provider_error.__class__.__name__,
                error_message=str(provider_error),
                recoverable=is_retryable_error(provider_error),
            )

            # Re-raise the error
            raise provider_error from exc

    async def _create_stream_with_timeout(
        self,
        provider_request: Dict[str, Any],
        timeout: float,
        request_id: str,
    ) -> AsyncIterator[Any]:
        """
        Create provider stream with timeout handling.

        Args:
            provider_request: Provider-specific request
            timeout: Timeout in seconds
            request_id: Request ID for logging

        Returns:
            Provider-specific stream

        Raises:
            TimeoutError: If stream creation times out
        """
        logger.debug(
            "provider.stream.create",
            request_id=request_id,
            timeout=timeout,
        )

        try:
            stream = await asyncio.wait_for(
                self._create_stream(provider_request),
                timeout=timeout,
            )
            return stream
        except asyncio.TimeoutError as exc:
            logger.error(
                "provider.stream.timeout",
                request_id=request_id,
                timeout=timeout,
            )
            raise TimeoutError(
                f"Stream creation timed out after {timeout}s",
                provider_name=self.provider_config.provider_name,
                timeout_seconds=timeout,
            ) from exc

    async def _create_stream(
        self, provider_request: Dict[str, Any]
    ) -> AsyncIterator[Any]:
        """
        Create provider-specific stream.

        This is the main method that concrete providers must implement.
        It should create and return the provider's native stream object.

        Args:
            provider_request: Provider-specific request dictionary

        Returns:
            Provider-specific stream iterator

        Raises:
            Provider-specific exceptions for network errors, etc.
        """
        raise NotImplementedError(
            "Concrete providers must implement _create_stream method"
        )

    def _log_response(self, response: LLMResponse, request_id: str) -> None:
        """
        Log response for debugging and monitoring.

        Args:
            response: LLM response object
            request_id: Request ID for correlation
        """
        from ..chat.response_types import (
            ResponseType,
        )

        # Only log certain response types to avoid noise
        if response.type in {
            ResponseType.TOOL_CALL_START_DELTA,
            ResponseType.TOOL_CALL_COMPLETE_DELTA,
            ResponseType.FINAL_RESPONSE,
            ResponseType.ERROR_RESPONSE,
        }:
            logger.debug(
                "provider.response",
                request_id=request_id,
                response_type=response.type.value,
                response=str(response),
            )
