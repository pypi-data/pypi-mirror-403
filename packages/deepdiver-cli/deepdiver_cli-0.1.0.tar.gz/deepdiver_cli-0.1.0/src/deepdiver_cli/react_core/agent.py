from __future__ import annotations

from typing import Any, Dict, List, Optional
import structlog

from deepdiver_cli.chat.chat_model import (
    LLMMessage,
    LLMRole,
    make_assistant_message,
    make_sys_message,
    make_tool_message,
    make_user_message,
)
from deepdiver_cli.chat.response_types import FinalResponse, ToolCall

from .llm import LLMClient
from .tool import ToolRegistry, ToolError, ToolRet
from .prompt import system_prompt
from deepdiver_cli.utils.font_style import GRAY_NORMAL, RESET, WHITE_BOLD

logger = structlog.get_logger(__name__)

stuck_reminder = "Observed duplicate responses. Consider new strategies and avoid repeating ineffective paths already attempted."
finish_reminder = "No **Tool Calling** but only reasonging(or answer), somthing wrong? If you have finish the task，you should call `Finish` tool before output the final answer."


class ReActAgentConfig:
    def __init__(
        self,
        max_steps: int = 30,
        allow_tool_hallucination: bool = False,
        dump_observation: bool = True,
        dump_tool_call: bool = True,
        finish_tool_name: str = "",
        duplicate_threshold: int = 2,
    ):
        self.max_steps = max_steps
        self.allow_tool_hallucination = allow_tool_hallucination
        self.dump_observation = dump_observation
        self.dump_tool_call = dump_tool_call
        self.finish_tool_name = finish_tool_name
        self.duplicate_threshold = duplicate_threshold


class ReActAgent:
    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        config: Optional[ReActAgentConfig] = None,
    ):
        self.llm = llm
        self.tools = tools
        self.config = config or ReActAgentConfig()
        self.trajectory_msgs: List[LLMMessage] = []
        self.should_finish = False

    async def aask(self, user_query: str) -> Dict[str, Any]:
        """
        Run a full ReAct loop for a single query.
        Returns:
          - final_answer: str
          - steps: list of dicts with thought/action/observation
        """

        # Rest state
        self.should_finish = False

        # Seed conversation with system + user messages
        system = system_prompt()
        self.trajectory_msgs.append(make_sys_message(system))
        self.trajectory_msgs.append(make_user_message(user_query))

        for step_idx in range(1, self.config.max_steps + 1):
            logger.info("agent.step.start", step=step_idx)

            rsp = await self._step()

            if rsp is None:
                logger.warning("agent.step.response_is_null", step=step_idx)
                continue

            if rsp.tool_calls:
                # Add assistant message back to loop
                assistant_msg = make_assistant_message(
                    content=rsp.content,
                    reasoning=rsp.reasoning,
                    tool_calls=rsp.tool_calls,
                )

                self.trajectory_msgs.append(assistant_msg)

                await self._call_tools(rsp.tool_calls)

                # Check if stucked
                if self._is_stuck():
                    self._handle_stuck(step_idx)

                continue
            elif not self.should_finish:
                logger.warning("agent.step.no_toocall", step=step_idx)
                reminder_msg = make_user_message(
                    self._build_system_reminder_message(finish_reminder)
                )
                self.trajectory_msgs.append(reminder_msg)
                continue
            else:
                logger.info(
                    "agent.step.final", step=step_idx, should_finish=self.should_finish
                )
                return {"final_answer": rsp.content.strip()}

        # Max steps reached: force finalization
        logger.warning("agent.max_steps_reached", max_steps=self.config.max_steps)
        return {
            "final_answer": "I'm stopping due to step limit. Here is my best answer based on the progress above.",
        }

    async def _step(self) -> FinalResponse:
        return await self.llm.step(
            messages=self.trajectory_msgs, tools=self.tools.as_llm_tools()
        )

    async def _call_tools(self, tool_calls: List[ToolCall]):
        for tool_call in tool_calls:
            self._dump_toolcall(tool_call.name, tool_call.arguments)

            tool_ret = await self._call_tool(tool_call)

            self._dump_toolret(tool_call.name, tool_ret)
            tool_ret.human_readable_content = None

            self.trajectory_msgs.append(
                make_tool_message(
                    tool_ret.model_dump_json(exclude_none=True),
                    tool_call.id,
                    tool_call.name,
                )
            )

            if self._is_finish_tool_call(tool_call.name):
                logger.info("agent.finishtask")
                self.should_finish = True

    async def _call_tool(self, tool_call: ToolCall) -> ToolRet:
        tool_name = tool_call.name
        # Validate tool
        try:
            tool = self.tools.get(tool_name)
        except ToolError:
            logger.warning(
                "agent.tool_calling_error",
                tool_name=tool_name,
                error_msg="Unknown tool:{tool_name}",
            )
            return ToolRet(
                success=False,
                summary=f"Tool is not available. Available: {', '.join(self.tools.list_names())}. Continue.",
                meta={"tool_name": tool_name},
            )

        # Call tool
        try:
            return await tool.call(tool_call.arguments)
        except ToolError as e:
            logger.error(
                "agent.tool_calling_error", tool_name=tool_name, error_msg=f"{e!r}"
            )
            return ToolRet(
                success=False,
                summary="Tool calling error",
                meta={"tool_name": tool_name},
                error={"msg": f"{e!r}"},
            )
        except Exception as e:
            logger.error(
                "agent.tool_calling_error", tool_name=tool_name, error_msg=f"{e!r}"
            )
            return ToolRet(
                success=False,
                summary="Tool calling error",
                meta={"tool_name": tool_name},
                error={"msg": f"{e!r}"},
            )

    def _is_finish_tool_call(self, tool_name) -> bool:
        return self.config.finish_tool_name == tool_name

    def _is_stuck(self) -> bool:
        """Check if the agent is stuck in a loop by detecting duplicate content"""
        if len(self.trajectory_msgs) < 2:
            return False

        def get_reasoning_content(msg) -> str:
            if hasattr(msg, "reasoning_detail"):
                return msg.reasoning_detail.content
            return ""

        last_message = self.trajectory_msgs[-1]
        if not last_message.content:
            return False
        if not get_reasoning_content(last_message):
            return False

        # Count identical content occurrences
        duplicate_count = sum(
            1
            for msg in reversed(self.trajectory_msgs[:-1])
            if (
                msg.role == LLMRole.ASSISTANT
                and msg.content == last_message.content
                and get_reasoning_content(msg) == get_reasoning_content(last_message)
            )
        )
        return duplicate_count >= self.config.duplicate_threshold

    def _handle_stuck(self, step):
        logger.warning("agent.stucked", step=step)
        reminder_msg = make_user_message(
            self._build_system_reminder_message(stuck_reminder)
        )
        self.trajectory_msgs.append(reminder_msg)

    def _build_system_reminder_message(self, content):
        return f"<system-reminder>{content}</system-reminder>"

    def _dump_toolret(self, tool_name: str, tool_ret: ToolRet):
        if self.config.dump_observation and self.tools.should_dump_toolret(tool_name):
            print(
                f"\n{WHITE_BOLD}{tool_name}Response:\n{RESET}{GRAY_NORMAL}{self._get_human_readable(tool_ret)}{RESET}"
            )
        else:
            print(f"\n{WHITE_BOLD}{tool_name}Response:\n{RESET}{GRAY_NORMAL}...{RESET}")

    def _get_human_readable(self, tool_ret: ToolRet) -> str:
        human_readable = tool_ret.human_readable_content or tool_ret.summary or ""
        return f"{human_readable}"

    def _dump_toolcall(self, tool_name, arguments):
        if self.config.dump_tool_call:
            max = 400
            dump_content = (
                f"{arguments[:max]}\n..." if len(arguments) > max else arguments
            )
            print(
                f"{WHITE_BOLD}{tool_name}:\n{RESET}{GRAY_NORMAL}{dump_content}{RESET}"
            )
