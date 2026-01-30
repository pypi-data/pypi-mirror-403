import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple, override

from pydantic import Field

from deepdiver_cli.config import config
from deepdiver_cli.app.processor import get_desensitizer
from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.utils.file_util import is_within_dirs
from deepdiver_cli.utils.log_filter import apply_time_filter
from deepdiver_cli.utils.time_util import is_time_format
from deepdiver_cli.utils.truncate_util import truncate_text
from deepdiver_cli.utils.grep_util import Rg, SearchCmdBuilder, SearchResult


def shift_time(time_str, seconds=-1):
    """
    将给定的时间字符串前后移动指定的秒数。

    参数:
        time_str (str): 时间字符串，格式为 "HH:MM:SS"
        seconds (int): 移动的秒数，负数表示向前，正数表示向后

    返回:
        str: 移动后的时间字符串，格式为 "HH:MM:SS"
    """
    dt = datetime.strptime(time_str, "%H:%M:%S")
    shifted = dt + timedelta(seconds=seconds)
    return shifted.strftime("%H:%M:%S")


# 可用区间
def get_available_time_range(
    actual_time_range: Tuple[str, str],
    expected_time_range: Tuple[str, str],
) -> List[str]:
    # 拆解变量，避免后续再用索引
    actual_start, actual_end = actual_time_range
    expected_start, expected_end = expected_time_range
    # 不重合
    expected_start = shift_time(expected_start, -1)
    expected_end = shift_time(expected_end, 1)

    available: List[Tuple[str, str]] = []

    # case 1: 实际区间完全在期望区间左侧
    if actual_start <= expected_start and actual_end <= expected_end:
        available.append((actual_start, expected_start))

    # case 2: 实际区间完全在期望区间右侧
    if actual_start >= expected_end:
        available.append((actual_start, actual_end))

    # case 3: 实际区间完全覆盖期望区间
    if actual_start <= expected_start and actual_end >= expected_end:
        available.append((actual_start, expected_start))
        available.append((expected_end, actual_end))

    # 统一格式化成字符串
    return [f"{start} - {end}" for start, end in available]


def is_time_range_valid(time_range: str) -> bool:
    if len(time_range.split("-")) == 2:
        times = time_range.split("-")
        return is_time_format(times[0]) and is_time_format(times[1])
    return False


class GrepInput(ToolInput):
    paths: List[str] = Field(
        description="要搜索的路径列表。每一项可以是文件路径或目录路径。"
    )
    pattern: str = Field(
        description=(
            "搜索模式（通常为正则表达式或简单字符串，具体行为取决于后端 ripgrep 配置）。"
        )
    )
    glob: Optional[List[str]] = Field(
        default=[],
        description=(
            "文件过滤的 glob 模式列表（相对于每个 path）。"
            "例如 ['**/*.log', '**/*.trace']。为空或缺省时不过滤。"
        ),
    )
    ignore_case: Optional[bool] = Field(
        default=None,
        description="是否忽略大小写，相当于 ripgrep 的 -i。默认 False。",
    )
    case_sensitive: Optional[bool] = Field(
        default=None,
        description="是否大小写敏感，相当于 ripgrep 的 -s。通常不需要与 ignore_case 同时使用。",
    )
    context: Optional[int] = Field(
        default=None,
        description="匹配行前后各返回多少行上下文，相当于 ripgrep 的 -C。",
    )
    before_context: Optional[int] = Field(
        default=None,
        description="匹配行前返回多少行上下文，相当于 ripgrep 的 -B。",
    )
    after_context: Optional[int] = Field(
        default=None,
        description="匹配行后返回多少行上下文，相当于 ripgrep 的 -A。",
    )
    # max_count: Optional[int] = Field(
    #     default=None,
    #     description="最多返回的匹配条数上限，用于防止结果过大，相当于 ripgrep 的 -m。",
    # )
    time_range: Optional[str] = Field(
        default=None,
        description=(
            "日志时间窗口，仅对带时间戳的日志有意义，**格式**为: `HH:mm:ss-HH:mm:ss`,例如：22:14:00-22:18:00"
        ),
    )


class GrepTool(BaseTool[GrepInput]):
    name = "Grep"
    description = (
        "基于 ripgrep 能力的通用文本搜索工具，可在一个或多个路径（文件/目录）中搜索模式，"
        "适用于日志、trace、配置、代码等文本文件。"
    )
    params = GrepInput
    timeout_s = 20.0

    def __init__(self, allow_dirs: Set[str]):
        super().__init__()
        self.truncate_config = config.truncate
        self.allow_dirs = allow_dirs
        self.seatcher = Rg(timeout_sec=int(self.timeout_s))

    @override
    async def __call__(self, params) -> ToolRet:
        if not params.paths:
            return ToolRet(success=False, summary="Parameter `paths ` is required")

        for path in params.paths:
            if not is_within_dirs(p=path, dirs=self.allow_dirs):
                return ToolRet(
                    success=False,
                    summary=f"Access denied: File must be within {self.allow_dirs}",
                )
        if params.time_range and not is_time_range_valid(params.time_range):
            return ToolRet(
                success=False,
                summary="Time range format is invalid, it should be HH:mm:ss-HH:mm:ss",
            )
        try:
            search_result: SearchResult = await self._search(params)
            if search_result.success:
                result = search_result.content

                # 搜索结果为空
                if not result:
                    return ToolRet(success=True, summary="Grep Result is empty")

                if result and params.time_range:
                    time_range_parts = params.time_range.split("-")
                    time_range = (time_range_parts[0], time_range_parts[1])
                    filter_result = apply_time_filter(result, time_range)
                    if (
                        not filter_result.content
                        and filter_result.content_start_time
                        and filter_result.content_end_time
                    ):
                        available_ranges = ",".join(
                            get_available_time_range(
                                (
                                    filter_result.content_start_time,
                                    filter_result.content_end_time,
                                ),
                                time_range,
                            )
                        )
                        print(result)
                        return ToolRet(
                            success=True,
                            summary=(
                                f"No matched logs found in {params.time_range} with the given pattern, matched logs is found in （{available_ranges}), it is recommended to refine grep parameters"
                            ),
                            data={"result": ""},
                        )
                    result = filter_result.content

                # 数据脱敏
                if result:
                    result = get_desensitizer().mask(result)

                if not result:
                    return ToolRet(
                        success=False, summary="Grep Result is empty after data masking"
                    )

                # 日志截断
                truncate_result = truncate_text(result, self.truncate_config.line_limit)

                summary = ""
                if truncate_result.is_omit:
                    summary = f"Grep result count reach limit {self.truncate_config.line_limit}, total {truncate_result.total_line_count} grep results, only {truncate_result.total_line_count - truncate_result.omit_line_count} results is returned, it is recommended to refine grep parameters. "
                else:
                    summary = f"Grep {truncate_result.total_line_count} result(s)."
                return ToolRet(
                    success=True,
                    summary=summary,
                    data={
                        "result": truncate_result.result,
                        "is_result_truncted": truncate_result.is_omit,
                        "total_count": truncate_result.total_line_count,
                        "return_count": truncate_result.total_line_count
                        - truncate_result.omit_line_count,
                    },
                )
            return ToolRet(success=False, summary=search_result.content)
        except asyncio.TimeoutError as e:
            return ToolRet(success=False, summary=f"Grep timeout: {e!r}")

    async def _search(self, params: GrepInput) -> SearchResult:
        cmd_builder = (
            SearchCmdBuilder(params.pattern)
            .paths(params.paths)
            .ignore_case(params.ignore_case is True)
            .case_sensitive(params.case_sensitive is True)
        )
        # 上下文选项
        if params.context is not None:
            cmd_builder.context(params.context)
        if params.before_context is not None:
            cmd_builder.before_context(params.before_context)
        if params.after_context is not None:
            cmd_builder.after_context(params.after_context)

        # 由truncate_config决定
        # 最大匹配数
        # if params.max_count is not None:
        #     cmd_builder.max_count(params.max_count)

        # glob 过滤
        if params.glob:
            cmd_builder.glob(params.glob)

        return await self.seatcher.search(cmd_builder.build())
