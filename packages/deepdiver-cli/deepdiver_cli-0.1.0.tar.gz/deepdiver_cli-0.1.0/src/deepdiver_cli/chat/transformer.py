"""
Abstract interfaces for request/response transformation.

This module defines abstract base classes for transforming between:
- LLMRequest/LLMMessage to provider-specific formats (RequestBuilder)
- Provider-specific responses to LLMResponse stream (ResponseParser)

Different providers can implement these interfaces to handle their specific API formats
while maintaining a unified interface for the rest of the system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from .chat_model import LLMMessage, LLMRequest, LLMToolSchema
from .response_types import (
    LLMResponse,
    ContentDelta,
    ReasoningDelta,
    ToolCallArgumentDelta,
    ToolCallCompleteDelta,
    UsageInfo,
)


class RequestBuilder(ABC):
    """
    Abstract interface for building provider-specific requests.

    Implementations of this interface handle the conversion from the
    unified LLMRequest format to provider-specific API request format.
    """

    @abstractmethod
    def build_request(self, request: LLMRequest) -> Dict[str, Any]:
        """
        Convert LLMRequest to provider-specific request format.

        Args:
            request: Unified LLM request

        Returns:
            Provider-specific request dictionary
        """
        raise NotImplementedError

    @abstractmethod
    def build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Convert LLMMessage list to provider-specific format.

        Args:
            messages: List of LLM messages

        Returns:
            List of provider-specific message dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def build_tools(
        self, tools: Optional[List[LLMToolSchema]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Convert LLMToolSchema list to provider-specific format.

        Args:
            tools: List of tool schemas, or None

        Returns:
            Provider-specific tool definitions, or None
        """
        raise NotImplementedError

    @abstractmethod
    def build_reasoning_config(
        self, enable_thinking: bool, extra_body: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Build reasoning configuration for provider.

        Args:
            enable_thinking: Whether thinking/reasoning is enabled
            extra_body: Existing extra_body configuration

        Returns:
            Provider-specific reasoning configuration, or None
        """
        raise NotImplementedError


class ResponseParser(ABC):
    """
    Abstract interface for parsing provider-specific responses.

    Implementations of this interface handle the conversion from
    provider-specific response streams to the unified LLMResponse format.
    """

    @abstractmethod
    async def parse_stream(
        self, stream: AsyncIterator[Any], request: LLMRequest
    ) -> AsyncIterator[LLMResponse]:
        """
        Parse provider-specific stream into standardized LLMResponse stream.

        This method should handle the entire streaming process, including:
        - Initializing accumulators for content, reasoning, tool calls
        - Parsing each chunk from the provider stream
        - Yielding appropriate LLMResponse objects (deltas and complete types)
        - Yielding a FinalResponse at the end of the stream

        Args:
            stream: Provider-specific response stream
            request: Original LLM request for context

        Yields:
            LLMResponse: Stream of standardized response objects
        """
        raise NotImplementedError

    @abstractmethod
    def parse_chunk(self, chunk: Any) -> List[LLMResponse]:
        """
        Parse a single provider chunk into LLMResponse objects.

        This method should extract all relevant information from a single
        provider response chunk and return appropriate LLMResponse objects.

        Args:
            chunk: Provider-specific response chunk

        Returns:
            List of LLMResponse objects extracted from the chunk
        """
        raise NotImplementedError

    def _accumulate_content(self, deltas: List[LLMResponse]) -> str:
        """
        Helper method to accumulate content from content deltas.

        Args:
            deltas: List of LLMResponse objects

        Returns:
            Accumulated content string
        """
        content = ""
        for delta in deltas:
            from .response_types import ContentDelta

            if isinstance(delta, ContentDelta):
                content += delta.chunk
        return content

    def _accumulate_reasoning(self, deltas: List[LLMResponse]) -> str:
        """
        Helper method to accumulate reasoning from reasoning deltas.

        Args:
            deltas: List of LLMResponse objects

        Returns:
            Accumulated reasoning string
        """
        reasoning = ""
        for delta in deltas:
            from .response_types import ReasoningDelta

            if isinstance(delta, ReasoningDelta):
                reasoning += delta.chunk
        return reasoning


# ============================================================================
# Base Implementations (Common Patterns)
# ============================================================================


class BaseRequestBuilder(RequestBuilder):
    """
    Base implementation with common patterns for RequestBuilder.

    Provides default implementations for common methods that can be
    overridden by specific providers as needed.
    """

    def build_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Default implementation building a standard request."""
        req_args: Dict[str, Any] = {
            "model": request.model,
            "messages": self.build_messages(request.messages),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True,  # Always stream in new design
        }

        # Add stream options if supported
        req_args["stream_options"] = {"include_usage": True}

        if request.tools:
            req_args["tools"] = self.build_tools(request.tools)
            req_args["tool_choice"] = request.tool_choice or "auto"
            req_args["parallel_tool_calls"] = request.parallel_tool_calls

        reasoning_config = self.build_reasoning_config(
            request.enable_thinking, request.extra_body
        )
        if reasoning_config:
            req_args["extra_body"] = reasoning_config
        elif request.extra_body:
            req_args["extra_body"] = request.extra_body

        return req_args

    def build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Default implementation converting all messages."""
        return [self.build_message(msg) for msg in messages]

    def build_message(self, message: LLMMessage) -> Dict[str, Any]:
        """
        Convert a single LLMMessage to provider-specific format.

        Default implementation can be overridden by providers for custom handling.

        Args:
            message: LLM message

        Returns:
            Provider-specific message dictionary
        """
        # Default implementation that can be overridden
        raise NotImplementedError(
            "Subclasses should implement build_message or override this method"
        )

    def build_tools(
        self, tools: Optional[List[LLMToolSchema]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Default implementation converting tools."""
        if not tools:
            return None
        return [self.build_tool(tool) for tool in tools]

    def build_tool(self, tool: LLMToolSchema) -> Dict[str, Any]:
        """
        Convert a single LLMToolSchema to provider-specific format.

        Default implementation can be overridden by providers for custom handling.

        Args:
            tool: LLMToolSchema

        Returns:
            Provider-specific tool dictionary
        """
        # Default implementation that can be overridden
        raise NotImplementedError(
            "Subclasses should implement build_tools or override this method"
        )


class BaseResponseParser(ResponseParser):
    """
    Base implementation with common patterns for ResponseParser.

    Provides common accumulation logic and state management for
    parsing provider streams into deltas and final responses.
    """

    def __init__(self):
        # State for accumulation during streaming
        self._content_acc = ""
        self._reasoning_acc = ""
        self._reasoning_raw_acc = None
        self._tool_calls_state: Dict[int, Dict[str, Any]] = {}
        self._usage: Optional[Dict[str, Any]] = None

    async def parse_stream(
        self, stream: AsyncIterator[Any], request: LLMRequest
    ) -> AsyncIterator[LLMResponse]:
        """
        Default stream parsing implementation.

        This implementation:
        1. Initializes accumulation state
        2. Processes each chunk from the stream
        3. Yields parsed deltas
        4. Yields FinalResponse at the end
        """
        # Reset state for new stream
        self._content_acc = ""
        self._reasoning_acc = ""
        self._reasoning_raw_acc = None
        self._tool_calls_state = {}
        self._usage = None

        try:
            async for chunk in stream:
                # Parse chunk into response objects
                responses = self.parse_chunk(chunk)

                # Update accumulators and yield responses
                for response in responses:
                    # Update accumulators based on response type
                    self._update_accumulators(response)

                    # Yield the response
                    yield response

        except Exception as exc:
            # Yield error response on exception
            from .response_types import ErrorResponse

            yield ErrorResponse(
                error_type=type(exc).__name__,
                error_message=str(exc),
                recoverable=False,
            )
            raise

        # Yield final response at the end
        from .response_types import FinalResponse, UsageInfo

        final_usage = None
        if self._usage:
            final_usage = (
                UsageInfo(**self._usage)
                if isinstance(self._usage, dict)
                else self._usage
            )

        yield FinalResponse(
            content=self._content_acc,
            reasoning=self._build_final_reasoning(),
            tool_calls=self._build_final_tool_calls(),
            usage=final_usage,
        )

    def _update_accumulators(self, response: LLMResponse) -> None:
        """Update accumulators based on response type."""

        if isinstance(response, ContentDelta):
            self._content_acc += response.chunk
        elif isinstance(response, ReasoningDelta):
            self._reasoning_acc += response.chunk
        elif isinstance(response, ToolCallArgumentDelta):
            # Update tool call arguments in state
            self._update_tool_call_argument(response)
        elif isinstance(response, ToolCallCompleteDelta):
            # Mark tool call as complete in state
            self._mark_tool_call_complete(response)
        elif isinstance(response, UsageInfo):
            self._usage = {
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
            }

    def _update_tool_call_argument(self, delta: ToolCallArgumentDelta) -> None:
        """Update tool call arguments in state."""
        # Default implementation - can be overridden
        pass

    def _mark_tool_call_complete(self, delta: ToolCallCompleteDelta) -> None:
        """Mark tool call as complete in state."""
        # Default implementation - can be overridden
        pass

    def _build_final_tool_calls(self):
        """Build final tool calls from state."""
        # Default implementation - can be overridden
        return []

    def _build_final_reasoning(self):
        """Build final reasoning from state."""
        # Default implementation - can be overridden
        from .response_types import Reasoning

        return Reasoning(text=self._reasoning_acc or "")

    def parse_chunk(self, chunk: Any) -> List[LLMResponse]:
        """
        Parse a single provider chunk.

        This is the main method that providers should override to handle
        their specific chunk format.

        Args:
            chunk: Provider-specific response chunk

        Returns:
            List of LLMResponse objects extracted from the chunk
        """
        # Base implementation returns empty list
        # Providers should override this method
        return []
