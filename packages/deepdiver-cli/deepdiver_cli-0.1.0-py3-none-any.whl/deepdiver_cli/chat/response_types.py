"""
Response type definitions for LLM streaming.

This module defines a comprehensive type system for LLM responses, including:
- Delta types: Incremental updates during streaming (ContentDelta, ReasoningDelta, etc.)
- Complete types: Full representations of response components (Content, Reasoning, etc.)
- LLMResponse: Union type that can be any of the above types

The design follows the principle of fine-grained streaming with semantic richness.
All types are designed to be immutable and serializable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ResponseType(Enum):
    """Enumeration of all possible response types."""

    CONTENT_DELTA = "content_delta"
    REASONING_DELTA = "reasoning_delta"
    TOOL_CALL_START_DELTA = "tool_call_start_delta"
    TOOL_CALL_ARGUMENT_DELTA = "tool_call_argument_delta"
    TOOL_CALL_COMPLETE_DELTA = "tool_call_complete_delta"
    CONTENT = "content"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    USAGE_INFO = "usage_info"
    FINAL_RESPONSE = "final_response"
    ERROR_RESPONSE = "error_response"


@dataclass
class BaseResponse:
    """Base class for all response types."""

    type: ResponseType
    timestamp: float = field(default_factory=lambda: time.time())

    def __str__(self) -> str:
        return f"{self.type.value}@{self.timestamp:.3f}"


# ============================================================================
# Delta Types (Incremental Updates)
# ============================================================================


@dataclass
class ContentDelta(BaseResponse):
    """Delta representing incremental content text."""

    type: ResponseType = ResponseType.CONTENT_DELTA
    chunk: str = ""
    index: int = 0  # For multi-turn conversations

    def __str__(self) -> str:
        return (
            f"{super().__str__()}: content_chunk[{self.index}]='{self.chunk[:50]}...'"
        )


@dataclass
class ReasoningDelta(BaseResponse):
    """Delta representing incremental reasoning text."""

    type: ResponseType = ResponseType.REASONING_DELTA
    chunk: str = ""
    raw: Optional[Any] = None
    index: int = 0
    reasoning_type: Optional[str] = None  # e.g., "text", "summary", "data"

    def __str__(self) -> str:
        return (
            f"{super().__str__()}: reasoning_chunk[{self.index}]='{self.chunk[:50]}...'"
        )


@dataclass
class ToolCallStartDelta(BaseResponse):
    """Delta indicating the start of a new tool call."""

    type: ResponseType = ResponseType.TOOL_CALL_START_DELTA
    tool_call_id: str = ""
    tool_name: str = ""
    index: int = 0

    def __str__(self) -> str:
        return f"{super().__str__()}: tool_start[{self.index}] id={self.tool_call_id} name={self.tool_name}"


@dataclass
class ToolCallArgumentDelta(BaseResponse):
    """Delta containing incremental tool call arguments."""

    type: ResponseType = ResponseType.TOOL_CALL_ARGUMENT_DELTA
    tool_call_id: str = ""
    argument_chunk: str = ""
    index: int = 0

    def __str__(self) -> str:
        return f"{super().__str__()}: tool_arg[{self.index}] id={self.tool_call_id} chunk='{self.argument_chunk[:50]}...'"


@dataclass
class ToolCallCompleteDelta(BaseResponse):
    """Delta indicating completion of a tool call with full arguments."""

    type: ResponseType = ResponseType.TOOL_CALL_COMPLETE_DELTA
    tool_call_id: str = ""
    tool_name: str = ""
    arguments: str = ""  # Complete arguments
    index: int = 0

    def __str__(self) -> str:
        return f"{super().__str__()}: tool_complete[{self.index}] id={self.tool_call_id} name={self.tool_name} args={self.arguments[:50]}..."


# ============================================================================
# Complete Types (Full Representations)
# ============================================================================


@dataclass
class Content(BaseResponse):
    """Complete content representation."""

    type: ResponseType = ResponseType.CONTENT
    text: str = ""
    index: int = 0

    def __str__(self) -> str:
        return f"{super().__str__()}: content[{self.index}]='{self.text[:100]}...'"


@dataclass
class Reasoning(BaseResponse):
    """Complete reasoning representation."""

    type: ResponseType = ResponseType.REASONING
    text: str = ""
    index: int = 0
    reasoning_type: Optional[str] = None
    raw: Optional[Any] = None

    def __str__(self) -> str:
        return f"{super().__str__()}: reasoning[{self.index}]='{self.text[:100]}...'"


@dataclass
class ToolCall(BaseResponse):
    """Complete tool call representation."""

    type: ResponseType = ResponseType.TOOL_CALL
    id: str = ""
    name: str = ""
    arguments: str = ""
    index: int = 0
    raw: Optional[Any] = None

    def __str__(self) -> str:
        return f"{super().__str__()}: tool_call[{self.index}] id={self.id} name={self.name}"


@dataclass
class UsageInfo(BaseResponse):
    """Token usage information."""

    type: ResponseType = ResponseType.USAGE_INFO
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __str__(self) -> str:
        return f"{super().__str__()}: usage prompt={self.prompt_tokens} completion={self.completion_tokens} total={self.total_tokens}"


@dataclass
class FinalResponse(BaseResponse):
    """
    Final response containing aggregated data.

    This type represents the complete response after streaming ends.
    It aggregates all deltas received during the stream.
    """

    type: ResponseType = ResponseType.FINAL_RESPONSE
    content: str = ""
    reasoning: Optional[Reasoning] = None
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[UsageInfo] = None

    def __str__(self) -> str:
        tool_count = len(self.tool_calls) if self.tool_calls else 0
        return f"{super().__str__()}: final content_len={len(self.content)} reasoning_len={len(self.reasoning.text) if self.reasoning else 0} tools={tool_count}"


@dataclass
class ErrorResponse(BaseResponse):
    """Error response containing error information."""

    type: ResponseType = ResponseType.ERROR_RESPONSE
    error_type: str = ""
    error_message: str = ""
    recoverable: bool = False
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{super().__str__()}: error {self.error_type}: {self.error_message}"


# ============================================================================
# Union Type
# ============================================================================

LLMResponse = Union[
    # Delta types
    ContentDelta,
    ReasoningDelta,
    ToolCallStartDelta,
    ToolCallArgumentDelta,
    ToolCallCompleteDelta,
    # Complete types
    Content,
    Reasoning,
    ToolCall,
    UsageInfo,
    FinalResponse,
    ErrorResponse,
]


# ============================================================================
# Utility Functions
# ============================================================================


def is_delta(response: LLMResponse) -> bool:
    """Check if a response is a delta (incremental update)."""
    return response.type in {
        ResponseType.CONTENT_DELTA,
        ResponseType.REASONING_DELTA,
        ResponseType.TOOL_CALL_START_DELTA,
        ResponseType.TOOL_CALL_ARGUMENT_DELTA,
        ResponseType.TOOL_CALL_COMPLETE_DELTA,
    }


def is_complete(response: LLMResponse) -> bool:
    """Check if a response is a complete (non-delta) type."""
    return response.type in {
        ResponseType.CONTENT,
        ResponseType.REASONING,
        ResponseType.TOOL_CALL,
        ResponseType.USAGE_INFO,
        ResponseType.FINAL_RESPONSE,
        ResponseType.ERROR_RESPONSE,
    }


def is_final(response: LLMResponse) -> bool:
    """Check if a response is a final response."""
    return response.type == ResponseType.FINAL_RESPONSE


def is_error(response: LLMResponse) -> bool:
    """Check if a response is an error response."""
    return response.type == ResponseType.ERROR_RESPONSE


def build_legacy_response(final_response: FinalResponse) -> Dict[str, Any]:
    """
    Build a legacy LLMResponse-like dictionary from a FinalResponse.

    This is a temporary compatibility function to help with migration.
    """
    from .chat_model import LLMResoningDetail, LLMToolCall

    # Convert tool calls to legacy format
    tool_calls = None
    if final_response.tool_calls:
        tool_calls = [
            LLMToolCall(
                id=tool.id,
                name=tool.name,
                arguments=tool.arguments,
                raw=tool.raw,
            )
            for tool in final_response.tool_calls
        ]

    # Convert reasoning to legacy format
    reasoning_detail = None
    if final_response.reasoning:
        reasoning_detail = LLMResoningDetail(
            content=final_response.reasoning,
            raw=None,  # Can be populated if needed
        )

    return {
        "content": final_response.content,
        "reasoning_detail": reasoning_detail,
        "tool_calls": tool_calls,
        "usage": final_response.usage,
        "is_final": True,
    }
