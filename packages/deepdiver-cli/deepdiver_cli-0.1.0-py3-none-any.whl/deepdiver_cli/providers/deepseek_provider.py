from openai import AsyncOpenAI
import structlog
from deepdiver_cli.chat.chat_model import LLMMessage, AssistantMessage

from typing import Any, AsyncIterator, Dict, List, Optional
from deepdiver_cli.chat.response_types import (
    LLMResponse,
    ContentDelta,
    ReasoningDelta,
    ToolCallStartDelta,
    ToolCallArgumentDelta,
    UsageInfo,
)
from deepdiver_cli.providers.base_provider import BaseProvider
from deepdiver_cli.providers.openrouter_provider import (
    OpenRouterRequestBuilder,
    OpenRouterResponseParser,
    OpenRouterProvider,
)


logger = structlog.get_logger(__name__)


class DeepSeekProvider(BaseProvider):
    """
    This provider inherits from BaseProvider and uses DeepSeek-specific
    transformers for handling DeepSeek's API differences.
    """

    # Use same retryable exceptions as OpenRouter
    retryable_exceptions = OpenRouterProvider.retryable_exceptions

    def __init__(self, provider_config, request_builder=None, response_parser=None):
        request_builder = request_builder or DeepSeekRequestBuilder()
        response_parser = response_parser or DeepSeekResponseParser()
        super().__init__(provider_config, request_builder, response_parser)

        self.client = AsyncOpenAI(
            api_key=provider_config.api_key, base_url=provider_config.base_url
        )

    async def _create_stream(
        self, provider_request: Dict[str, Any]
    ) -> AsyncIterator[Any]:
        """Create DeepSeek stream (same as OpenRouter)."""
        return await self.client.chat.completions.create(**provider_request)


# ============================================================================
# DeepSeek Transformer Classes
# ============================================================================


class DeepSeekRequestBuilder(OpenRouterRequestBuilder):
    """Request builder for DeepSeek API."""

    def build_message(self, message: LLMMessage) -> Dict[str, Any]:
        """Convert LLMMessage to DeepSeek format."""
        if isinstance(message, AssistantMessage):
            return {
                "role": "assistant",
                "content": message.content,
                "reasoning_content": (
                    message.reasoning.text if message.reasoning else ""
                ),
                "tool_calls": [
                    tool_call.raw
                    for tool_call in (message.tool_calls or [])
                    if message.tool_calls
                ],
            }
        return super().build_message(message)

    def build_reasoning_config(
        self, enable_thinking: bool, extra_body: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Build reasoning configuration for DeepSeek."""
        if not enable_thinking:
            return extra_body

        extra_body = extra_body or {}
        if extra_body.get("thinking") is None:
            extra_body["thinking"] = {"type": "enabled"}
        return extra_body


class DeepSeekResponseParser(OpenRouterResponseParser):
    """Response parser for DeepSeek API."""

    def parse_chunk(self, chunk: Any) -> List[LLMResponse]:
        """Parse DeepSeek chunk into response objects."""
        responses: List[LLMResponse] = []

        # Check for usage information
        if hasattr(chunk, "usage") and chunk.usage:
            responses.append(
                UsageInfo(
                    prompt_tokens=chunk.usage.prompt_tokens or 0,
                    completion_tokens=chunk.usage.completion_tokens or 0,
                    total_tokens=chunk.usage.total_tokens or 0,
                )
            )
            return responses

        # Skip if no choices
        if not hasattr(chunk, "choices") or not chunk.choices:
            return responses

        delta = chunk.choices[0].delta

        # Parse content
        if hasattr(delta, "content") and delta.content:
            responses.append(ContentDelta(chunk=delta.content))

        # Parse reasoning (DeepSeek uses reasoning_content instead of reasoning_details)
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            responses.append(
                ReasoningDelta(chunk=delta.reasoning_content, reasoning_type="text")
            )

        # Parse tool calls (same as OpenRouter)
        if hasattr(delta, "tool_calls") and delta.tool_calls:
            for tool_delta in delta.tool_calls:
                index = getattr(tool_delta, "index", 0)
                tool_id = getattr(tool_delta, "id", "")
                fn = getattr(tool_delta, "function", None)

                # Extract function name and arguments safely
                fn_name = ""
                fn_arguments = ""
                if fn is not None:
                    if isinstance(fn, dict):
                        fn_name = fn.get("name", "")
                        fn_arguments = fn.get("arguments", "")
                    else:
                        # Assume object with name and arguments attributes
                        fn_name = getattr(fn, "name", "")
                        fn_arguments = getattr(fn, "arguments", "")

                # Handle tool call start
                if tool_id and fn_name:
                    # Check if this tool call is new
                    if (
                        index not in self._tool_calls_state
                        or self._tool_calls_state[index].get("id") != tool_id
                    ):
                        responses.append(
                            ToolCallStartDelta(
                                tool_call_id=tool_id,
                                tool_name=fn_name,
                                index=index,
                            )
                        )
                        # Initialize accumulation state (compatible with OpenRouter format)
                        self._tool_calls_state[index] = {
                            "id": tool_id,
                            "type": getattr(tool_delta, "type", "function"),
                            "function": {
                                "name": fn_name,
                                "arguments": "",
                            },
                        }

                # Handle tool call arguments
                if fn_arguments:
                    responses.append(
                        ToolCallArgumentDelta(
                            tool_call_id=tool_id,
                            argument_chunk=fn_arguments,
                            index=index,
                        )
                    )

        return responses
