from pathlib import Path
from typing import List, Optional, Set, override
from pydantic import Field
from deepdiver_cli.config import config
from deepdiver_cli.chat.chat_model import (
    LLMMessage,
    make_sys_message,
    make_user_message,
)
from deepdiver_cli.react_core.llm import LLMClient
from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.utils.grep_util import Rg, SearchCmdBuilder
from deepdiver_cli.utils.log_filter import apply_time_filter
from deepdiver_cli.utils.log_sorter import sort_logs_with_stacktrace
from deepdiver_cli.utils.truncate_util import truncate_text
from deepdiver_cli.utils.file_util import is_within_dirs, read_text
from deepdiver_cli.app.processor import get_desensitizer
import structlog

logger = structlog.get_logger(__name__)

INSPECT_LOG_PROMPT_FILE = config.prompt_dir / "inspector.md"


class InspectInput(ToolInput):
    path: str = Field(description="日志文件路径")
    knowledge_key: Optional[list[str]] = Field(
        default=[], description="当前使用到的知识类型 key 列表"
    )
    pattern: Optional[str] = Field(description="grep 兼容正则，用于统计的关键字/模式。")
    max_count: Optional[int] = Field(default=100, description="grep搜索结果数量上限")
    time_range: Optional[str] = Field(
        default=None,  # 默认值为None，表示不启用时间过滤
        description="时间范围，格式为 HH:mm:ss-HH:mm:ss",
    )


class InspectTool(BaseTool[InspectInput]):
    name = "Inspect"
    description = (
        "在给定时间窗口内扫描日志的错误密度/异常分布/事件分布，用于缩小排查范围。"
    )
    params = InspectInput
    timeout_s = 20

    def __init__(
        self,
        allow_dirs: Set[str],
    ) -> None:
        super().__init__()
        self.inspect_config = config.tools.inspect
        self.truncate_config = config.truncate
        self.allow_dirs = allow_dirs
        self.llm = LLMClient(self.inspect_config.llm)
        self.searcher = Rg(timeout_sec=int(self.timeout_s))

    @override
    async def __call__(self, params) -> ToolRet:
        if not is_within_dirs(params.path, self.allow_dirs):
            return ToolRet(
                success=False,
                summary=f"Access denied: File must be within {self.allow_dirs}",
            )
        raw_path = Path(params.path)

        if not raw_path.exists():
            return ToolRet(
                success=False,
                summary=f"error: file '{raw_path}' does not exist",
            )
        if not raw_path.is_file():
            return ToolRet(success=False, summary=f"error: '{raw_path}' is not a file")

        # Process configured patterns
        config_results = await self._process_config_patterns(params)

        # Process custom pattern if provided
        custom_results = await self._process_custom_pattern(params)

        # Combine and deduplicate results
        content = self._deduplicate_and_process(config_results + custom_results)

        # Apply final truncation and prepare for output
        truncated_lines, is_any_line_truncted = self._prepare_output(content)

        logger.info(
            "inspectlog.dump",
            category="Total",
            line_count=len(truncated_lines),
            is_any_line_truncted=is_any_line_truncted,
        )
        # 排序
        sorted_log = sort_logs_with_stacktrace("\n".join(truncated_lines))
        if sorted_log:
            print(sorted_log)
            inspect_result = await self._inspect_log(sorted_log)

            return ToolRet(
                success=True,
                summary="Inspect success",
                data=inspect_result,
                human_readable_content=inspect_result,
            )
        return ToolRet(success=True, summary="No ispect result")

    async def _inspect_log(self, log: str) -> str:
        """
        inspect log
        """
        logger.info("llm.insepectlog.start")
        trajectory_msgs: List[LLMMessage] = []
        trajectory_msgs.append(make_sys_message(self._get_sys_prompt()))
        trajectory_msgs.append(make_user_message(log))
        rsp = await self.llm.step(messages=trajectory_msgs)
        return rsp.content

    def _get_sys_prompt(self) -> str:
        prompt = read_text(INSPECT_LOG_PROMPT_FILE)
        if not prompt:
            raise ValueError("System prompt is empty")
        return prompt

    async def _process_config_patterns(self, params) -> List[str]:
        """Process all configured pattern configurations."""
        results = []
        for pattern_config in self.inspect_config.patterns:
            # Join all patterns in this configuration with "|"
            if not pattern_config.patterns:
                continue

            # Combine patterns with OR operator
            combined_pattern = "|".join(pattern_config.patterns)

            # Determine line limit for this pattern configuration
            pattern_line_limit = (
                min(pattern_config.line_limit, self.inspect_config.line_limit)
                if pattern_config.line_limit is not None
                else self.inspect_config.line_limit
            )

            # Apply time filter if configured
            time_range_to_use = (
                params.time_range if pattern_config.apply_time_filter else None
            )

            # Perform search with combined pattern
            raw_result = await self._search(
                params.path,
                combined_pattern,
                before=pattern_config.before_context,
                after=pattern_config.after_context,
                time_range=time_range_to_use,
            )

            # Apply pattern-specific line limit
            if raw_result:
                truncate_result = truncate_text(raw_result, pattern_line_limit)
                results.append(truncate_result.result)
            else:
                results.append("")

        return results

    async def _process_custom_pattern(self, params) -> List[str]:
        """Process custom pattern provided by user."""
        if not params.pattern:
            return []

        raw_result = await self._search(
            params.path, params.pattern, time_range=params.time_range
        )
        if raw_result:
            truncate_result = truncate_text(raw_result, params.max_count)
            return [truncate_result.result]
        return [""]

    def _deduplicate_and_process(self, results: List[str]) -> str:
        """Deduplicate lines and apply desensitization."""
        # Deduplicate: collect all lines and remove duplicates
        seen_lines = set()
        unique_lines = []
        for result in results:
            if not result:
                continue
            for line in result.splitlines():
                if line not in seen_lines:
                    seen_lines.add(line)
                    unique_lines.append(line)

        content = "\n".join(unique_lines)
        if content:
            content = get_desensitizer().mask(content)

        return content

    def _prepare_output(self, content: str):
        """Apply final truncation and prepare output."""
        if content:
            truncate_result = truncate_text(content, self.inspect_config.line_limit)
            content = truncate_result.result
            is_any_line_truncted = truncate_result.is_line_truncted
            truncated_lines = content.splitlines()
        else:
            truncated_lines = []
            is_any_line_truncted = False

        return truncated_lines, is_any_line_truncted

    async def _search(
        self, path: str, pattern: str, before=0, after=0, time_range=None
    ) -> str:
        if not pattern:
            return ""

        cmd_builder = (
            SearchCmdBuilder(pattern)
            .paths([path])
            .before_context(before)
            .after_context(after)
        )
        search_result = await self.searcher.search(cmd_builder.build())
        if time_range and search_result.success and search_result.content:
            return apply_time_filter(search_result.content, time_range).content

        return search_result.content or ""
