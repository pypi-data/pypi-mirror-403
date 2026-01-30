from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from deepdiver_cli.chat.response_types import Reasoning, ToolCall


def make_sys_message(content: str) -> LLMMessage:
    return SystemMessage(content)


def make_assistant_message(
    content: str,
    reasoning: Reasoning | None,
    tool_calls: List[ToolCall] | None,
) -> LLMMessage:
    return AssistantMessage(content, reasoning, tool_calls)


def make_user_message(content) -> LLMMessage:
    return UserMessage(content)


def make_tool_message(content: str, tool_call_id: str, tool_name: str) -> LLMMessage:
    return ToolMessage(content, tool_call_id, tool_name)


class LLMRole(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"


class LLMMessage:
    def __init__(self, role: LLMRole, content: str):
        self.role = role
        self.content = content

    def __str__(self):
        return f"role={self.role} content={self.content}"


class UserMessage(LLMMessage):
    def __init__(self, content: str):
        super().__init__(LLMRole.USER, content)


class SystemMessage(LLMMessage):
    def __init__(self, content: str):
        super().__init__(LLMRole.SYSTEM, content)


class ToolMessage(LLMMessage):
    def __init__(self, content: str, tool_call_id: str, tool_name: str):
        super().__init__(LLMRole.TOOL, content)
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name

    def __str__(self):
        return f"role={self.role} content={self.content} tool_call_id={self.tool_call_id} tool_name={self.tool_name}"


class AssistantMessage(LLMMessage):
    def __init__(
        self,
        content: str,
        reasoning: Reasoning | None,
        tool_calls: List[ToolCall] | None,
    ):
        super().__init__(LLMRole.ASSISTANT, content)
        self.reasoning = reasoning
        self.tool_calls = tool_calls

    def __str__(self):
        tools = ",".join([tool_call.name for tool_call in (self.tool_calls or [])])
        reasoning_detail_raw = (
            self.reasoning.raw if self.reasoning else None
        )
        return f"role={self.role} content={self.content} reasoning_detail={reasoning_detail_raw} tool_calls={tools} "


@dataclass
class LLMToolSchema:
    name: str
    description: str
    parameters: Dict


@dataclass
class LLMProviderConfig:
    provider_name: str
    base_url: str
    api_key: str


@dataclass
class LLMRequest:
    model: str
    messages: List[LLMMessage]
    enable_thinking: bool
    max_tokens: int
    temperature: float
    stream: bool
    timeout: float
    tools: Optional[List[LLMToolSchema]] = None
    tool_choice: Optional[str] = "auto"  # "auto" / "none" / specific tool name
    parallel_tool_calls: Optional[bool] = True
    extra_body: Optional[Dict[str, Any]] = None
