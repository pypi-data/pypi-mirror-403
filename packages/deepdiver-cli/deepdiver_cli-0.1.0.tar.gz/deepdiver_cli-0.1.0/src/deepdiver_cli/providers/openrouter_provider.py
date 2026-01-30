from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from openai import AsyncOpenAI
import openai

import structlog

from ..chat.chat_model import (
    AssistantMessage,
    LLMMessage,
    LLMRequest,
    SystemMessage,
    ToolMessage,
    LLMToolSchema,
    UserMessage,
)

from ..chat.response_types import (
    LLMResponse as NewLLMResponse,
    ContentDelta,
    Reasoning,
    ReasoningDelta,
    ToolCallStartDelta,
    ToolCallArgumentDelta,
    ToolCall,
    UsageInfo,
)
from ..chat.transformer import BaseRequestBuilder, BaseResponseParser
from ..chat.exceptions import TimeoutError
from ..providers.base_provider import BaseProvider

logger = structlog.get_logger(__name__)


class OpenRouterProvider(BaseProvider):
    """
    This provider uses OpenRouterRequestBuilder and OpenRouterResponseParser
    to handle OpenRouter/OpenAI compatible APIs with the new streaming interface.
    """

    retryable_exceptions = (
        TimeoutError,
        ConnectionError,
        httpx.TimeoutException,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError,
        openai.AuthenticationError,
        httpx.RemoteProtocolError,
    )

    def __init__(self, provider_config):
        request_builder = OpenRouterRequestBuilder()
        response_parser = OpenRouterResponseParser()
        super().__init__(provider_config, request_builder, response_parser)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=provider_config.api_key, base_url=provider_config.base_url
        )

    async def _create_stream(
        self, provider_request: Dict[str, Any]
    ) -> AsyncIterator[Any]:
        """Create OpenRouter stream."""
        return await self.client.chat.completions.create(**provider_request)


class OpenRouterRequestBuilder(BaseRequestBuilder):
    """Request builder for OpenRouter/OpenAI compatible APIs."""

    def build_message(self, message: LLMMessage) -> Dict[str, Any]:
        """Convert LLMMessage to OpenRouter format."""
        match message:
            case _ if isinstance(message, SystemMessage):
                return {
                    "role": "system",
                    "content": message.content,
                }
            case _ if isinstance(message, AssistantMessage):
                return {
                    "role": "assistant",
                    "content": message.content,
                    "reasoning_details": (
                        message.reasoning.raw if message.reasoning else None
                    ),
                    "tool_calls": [
                        tool_call.raw
                        for tool_call in (message.tool_calls or [])
                        if message.tool_calls
                    ],
                }
            case _ if isinstance(message, UserMessage):
                return {
                    "role": "user",
                    "content": message.content,
                }
            case _ if isinstance(message, ToolMessage):
                return {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            case _:
                raise ValueError(f"Unsupported message role: {message.role}")

    def build_tool(self, tool: LLMToolSchema) -> Dict[str, Any]:
        """Convert LLMToolSchema to OpenRouter format."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    def build_reasoning_config(
        self, enable_thinking: bool, extra_body: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Build reasoning configuration for OpenRouter."""
        if not enable_thinking:
            return extra_body

        extra_body = extra_body or {}
        if extra_body.get("reasoning") is None:
            extra_body["reasoning"] = {"enabled": True, "effort": "high"}
        return extra_body



class OpenRouterResponseParser(BaseResponseParser):
    """Response parser for OpenRouter/OpenAI compatible APIs."""

    def __init__(self):
        super().__init__()
        # Use parent class _tool_calls_state for accumulation

    async def parse_stream(
        self, stream: AsyncIterator[Any], request: LLMRequest
    ) -> AsyncIterator[NewLLMResponse]:
        """Parse stream with proper state reset."""
        # Reset tool calls state before starting new stream (parent also does this)
        self._tool_calls_state = {}
        # Call parent parse_stream which handles the rest
        async for response in super().parse_stream(stream, request):
            yield response

    def parse_chunk(self, chunk: Any) -> List[NewLLMResponse]:
        """Parse OpenRouter chunk into response objects."""
        responses: List[NewLLMResponse] = []
        
        # Check for usage information
        if hasattr(chunk, "usage") and chunk.usage:
            print(f"usage {chunk.usage}")
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

        # Parse reasoning
        if hasattr(delta, "reasoning_details") and delta.reasoning_details:
            # Extract reasoning content from raw data
            reasoning_content = self._extract_reasoning_content(delta.reasoning_details)
            if reasoning_content:
                responses.append(
                    ReasoningDelta(
                        chunk=reasoning_content,
                        raw=delta.reasoning_details,
                        reasoning_type="text",
                    )
                )

        # Parse tool calls
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
                        # Initialize accumulation state
                        tool_call = {
                            "id": tool_id,
                            "type": getattr(tool_delta, "type", "function"),
                            "function": {"name": fn_name, "arguments": ""},
                        }
                        self._tool_calls_state[index] = tool_call

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

    def _update_accumulators(self, response: NewLLMResponse) -> None:
        if isinstance(response, ReasoningDelta):
            self._reasoning_acc += response.chunk
            self._reasoning_raw_acc: List[Dict[str, Any]] = self._reasoning_raw_acc or []
            if isinstance(response.raw, dict):
                self._merge_reasoning_raw_by_index(self._reasoning_raw_acc, response.raw)
            elif isinstance(response.raw, list):
                for raw in response.raw:
                    if isinstance(raw, dict):
                        self._merge_reasoning_raw_by_index(self._reasoning_raw_acc, raw)
            return
        return super()._update_accumulators(response)

    def _merge_reasoning_raw_by_index(
        self, raws: List[Dict[str, Any]], raw: Dict[str, Any]
    ):
        """
        raw 包含 index、type、文本字段（text、summary）、其他字段。

        对于带有 index 的 raw，如果 raws 中已经存在同 index、同 type 的块，则进行字段级合并，而不是新增一条记录。

        返回一个合并后的 List[Dict[str, Any]]，对于 (index, type) 组合而言是唯一的，
        且 text、summary为累加结果。
        """

        # 查找是否已有同 index + type 的块
        target = None
        for item in raws:
            if item.get("index") == raw.get("index") and item.get("type") == raw.get(
                "type"
            ):
                target = item
                break

        if target is None:
            # 没有同 index + type，则直接追加
            raws.append(raw)
            return

        # ---------- 开始字段级合并 ----------

        # 1) text / summary 字段：做“累加”合并
        for key in ("text", "summary", "data"):
            if key not in raw:
                continue

            new_val = raw.get(key)
            if new_val is None:
                continue

            old_val = target.get(key)

            # 如果旧值为空，直接赋新值
            if old_val is None:
                target[key] = new_val
                continue

            # str：拼接
            if isinstance(old_val, str) and isinstance(new_val, str):
                target[key] = old_val + new_val

        # 2) 其他字段：简单规则合并
        #    - 如果 target 没有该字段，写入 raw 的值
        #    - 如果 target 有该字段但为 None，则写入 raw 的值
        #    - 两边都有非 None：保留原值（也可以改成覆盖，看业务需求）
        for k, v in raw.items():
            if k in ("index", "type", "text", "summary", "data"):
                continue
            if k not in target or target[k] in ("", None):
                target[k] = v

    def _extract_reasoning_content(self, reasoning_details: Any) -> str:
        """Extract reasoning text from reasoning_details."""
        if not reasoning_details:
            return ""

        content = ""

        if isinstance(reasoning_details, list):
            for item in reasoning_details:
                if isinstance(item, dict):
                    content += item.get("text") or item.get("summary") or ""
        elif isinstance(reasoning_details, dict):
            content = (
                reasoning_details.get("text") or reasoning_details.get("summary") or ""
            )
        elif isinstance(reasoning_details, str):
            content = reasoning_details

        return content

    def _update_tool_call_argument(self, delta: ToolCallArgumentDelta) -> None:
        """Update tool call arguments in state."""
        index = delta.index
        if index in self._tool_calls_state:
            self._tool_calls_state[index]["function"]["arguments"] += delta.argument_chunk

    def _build_final_tool_calls(self):
        """Build final tool calls from state."""

        tool_calls = []
        for index, acc in sorted(self._tool_calls_state.items()):
            tool_calls.append(
                ToolCall(
                    id=acc["id"],
                    name=acc["function"]["name"],
                    arguments=acc["function"]["arguments"],
                    index=index,
                    raw=acc,
                )
            )
        return tool_calls

    def _build_final_reasoning(self):
        """Build final_reasoning from state."""
        return Reasoning(text=self._reasoning_acc or "", raw=self._reasoning_raw_acc)
