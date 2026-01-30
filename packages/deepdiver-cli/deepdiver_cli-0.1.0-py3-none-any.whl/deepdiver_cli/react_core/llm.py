from __future__ import annotations


from typing import List, Optional

import structlog

from deepdiver_cli.config import LLMConfig
from deepdiver_cli.chat.chat_model import (
    LLMMessage,
    LLMRequest,
    LLMRole,
    ToolMessage,
    LLMToolSchema,
)
from deepdiver_cli.chat.chat_provider import ChatProvider
from deepdiver_cli.chat.chat_provider_factory import ChatProviderFactory

from deepdiver_cli.chat.response_types import (
    ContentDelta,
    ReasoningDelta,
    ToolCallStartDelta,
    ToolCallArgumentDelta,
    ToolCallCompleteDelta,
    UsageInfo,
    FinalResponse,
    ErrorResponse,
)

logger = structlog.get_logger(__name__)
dump_messages = False


def _maybe_print_header(title: str, condition: bool) -> None:
    if condition:
        print(f"\n{'=' * 20}{title}{'=' * 20}\n")


def _maybe_print_messages(messages: List[LLMMessage]):
    if not dump_messages:
        return
    for msg in messages:
        if msg.role == LLMRole.SYSTEM:
            continue
        if isinstance(msg, ToolMessage) and msg.tool_name == "LoadKnowledge":
            continue
        print(msg)


class LLMClient:
    """
    支持推理内容提取与工具调用的LLM客户端，可按需切换流式/非流式传输。
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self._chat_provider: ChatProvider = ChatProviderFactory.get_provider(
            llm_config.provider_name
        )

    async def step(
        self, messages: List[LLMMessage], tools: Optional[List[LLMToolSchema]] = None
    ) -> FinalResponse:
        logger.info(
            "llm.request",
            provider=self.llm_config.provider_name,
            model=self.llm_config.model,
            messages_count=len(messages),
            tools_count=len(tools) if tools else 0,
            stream=self.llm_config.stream,
        )

        request = LLMRequest(
            model=self.llm_config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=True,
            enable_thinking=self.llm_config.enable_thinking,
            max_tokens=self.llm_config.max_tokens,
            temperature=self.llm_config.temperature,
            stream=self.llm_config.stream,
            timeout=self.llm_config.timeout,
        )

        response = await self._step(request)
        # new line
        print("\n")

        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        tool_calls = ",".join(
            [tool_call.name for tool_call in (response.tool_calls or [])]
        )
        logger.info(
            "llm.response",
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        return response

    async def _step(self, request) -> FinalResponse:
        """
        Process LLM request using the new streaming architecture.

        This method uses the provider's generate() method to get a stream
        of LLMResponse objects (deltas and complete types), accumulates them,
        handles real-time printing, and returns the final response in the
        legacy format for compatibility.
        """
        _maybe_print_messages(request.messages)

        # Always use streaming in the new architecture
        # The provider's generate() method always returns a stream
        stream = self._chat_provider.generate(request)

        # State for printing
        is_thinking_printed = False
        is_answer_printed = False

        async for response in stream: 
            # Handle error responses
            if isinstance(response, ErrorResponse):
                logger.error(
                    "llm.stream.error",
                    error_type=response.error_type,
                    error_message=response.error_message,
                    recoverable=response.recoverable,
                )
                # if not response.recoverable:
                #     raise RuntimeError(
                #         f"{response.error_type}: {response.error_message}"
                #     )

            # Handle content deltas
            elif isinstance(response, ContentDelta):
                if self.llm_config.dump_answer:
                    if not is_answer_printed:
                        _maybe_print_header("完整回复", True)
                        is_answer_printed = True
                    print(response.chunk, end="", flush=True)

            # Handle reasoning deltas
            elif isinstance(response, ReasoningDelta):
                if request.enable_thinking and self.llm_config.dump_thinking:
                    if not is_thinking_printed:
                        _maybe_print_header("思考过程", True)
                        is_thinking_printed = True
                    print(response.chunk, end="", flush=True)

            # Handle tool call deltas
            elif isinstance(response, ToolCallStartDelta):
                logger.debug(
                    "llm.tool_call.start",
                    tool_call_id=response.tool_call_id,
                    tool_name=response.tool_name,
                    index=response.index,
                )

            elif isinstance(response, ToolCallArgumentDelta):
                pass

            elif isinstance(response, ToolCallCompleteDelta):
                pass

            # Handle usage information
            elif isinstance(response, UsageInfo):
                pass

            # Handle final response - end of stream
            elif isinstance(response, FinalResponse):
                return response

        # If we get here without a FinalResponse, something went wrong
        raise RuntimeError("Stream ended without FinalResponse")
