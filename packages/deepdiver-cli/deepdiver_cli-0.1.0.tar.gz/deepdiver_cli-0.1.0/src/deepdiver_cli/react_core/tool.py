from __future__ import annotations

from abc import ABC
import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
import structlog
import math

from deepdiver_cli.chat.chat_model import LLMToolSchema
from deepdiver_cli.utils.pydantic_tuil import parameters_from_input_model

logger = structlog.get_logger(__name__)


class ToolInput(BaseModel):
    """Base class for tool inputs; extend per tool."""


class ToolRet(BaseModel):
    success: bool
    data: Any = None
    error: Optional[Dict] = None
    summary: Optional[str] = None
    next_steps: Optional[List[str]] = None
    meta: Optional[Dict] = None
    human_readable_content: Optional[str] = None


class ToolCallResult(BaseModel):
    tool_call_id: str
    tool_name: str
    tool_ret: ToolRet


class ToolError(Exception):
    pass


class BaseTool[Params: ToolInput](ABC):
    """
    Base tool interface for ReAct.
    Each tool provides:
      - name: unique tool name
      - description: when to use this tool
      - input_model: a Pydantic model for input validation
      - __call__: async execution
    """

    name: str
    description: str
    params: type[Params]
    timeout_s: float = 15.0
    max_retries: int = 1
    dump_toolret: bool = True

    def __init__(self) -> None:
        if not hasattr(self, "name") or not hasattr(self, "description"):
            raise ValueError("Tool must define name and description")

    async def call(self, json_args: Any) -> ToolRet:
        function_args = {}
        try:
            function_args = json.loads(json_args)
        except json.JSONDecodeError as e:
            logger.error(
                "tool_call.arg_error",
                action=self.name,
                arguments=json_args,
            )
            raise ToolError(f"Tool arguments error: {e!r}, invalid json format") from e

        try:
            params = self.params.model_validate(function_args)
            return await self(params)
        except ValidationError as e:
            logger.error(
                "tool_call.arg_error",
                action=self.name,
                arguments=json_args,
            )
            raise ToolError(f"Invalid input for tool {self.name}: {e}")

    async def __call__(self, params: Params) -> ToolRet:
        raise NotImplementedError

    @classmethod
    def schema(cls) -> LLMToolSchema:
        return LLMToolSchema(
            name=cls.name,
            description=cls.description,
            parameters=parameters_from_input_model(cls.params),
        )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool name: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        return self._tools[name]

    def should_dump_toolret(self, name: str) -> bool:
        if name not in self._tools:
            return True
        return self._tools[name].dump_toolret

    def as_llm_tools(self) -> List[LLMToolSchema]:
        return [tool.schema() for tool in self._tools.values()]

    def list_names(self) -> Tuple[str, ...]:
        return tuple(self._tools.keys())

