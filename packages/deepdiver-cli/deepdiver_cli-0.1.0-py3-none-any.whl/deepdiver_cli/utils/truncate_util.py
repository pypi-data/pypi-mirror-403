from dataclasses import dataclass
from deepdiver_cli.app.processor import get_filter
from deepdiver_cli.config import config


@dataclass
class TruncateResult:
    result: str
    # 是否省略了某些行
    is_omit: bool = False
    # 总函数
    total_line_count: int = 0
    # 省略的行数
    omit_line_count: int = 0
    # 是否某行过长被截断
    is_line_truncted: bool = False


def truncate_text(text, max_lines) -> TruncateResult:
    """
    截断超过max_lines的日志

    Args:
        text: 日志文本字符串
        max_lines: 最大行数

    Returns:
        截断结果
    """
    if max_lines < 1:
        raise ValueError("n必须至少为1")

    # 处理空文本
    if not text or not text.strip():
        return TruncateResult(result=text, total_line_count=0)

    # Filter
    lines = [line for line in text.splitlines() if not _filter_line(line)]
    # Truncate
    is_line_truncted = False
    truncated_lines = []
    for line in lines:
        (is_truncted, result_line) = truncate_line(line)
        is_line_truncted = is_line_truncted or is_truncted
        truncated_lines.append(result_line)

    total_lines = len(truncated_lines)

    # 如果未超过限制，直接返回原文本
    if total_lines <= max_lines:
        return TruncateResult(
            result="\n".join(truncated_lines),
            total_line_count=total_lines,
            is_line_truncted=is_line_truncted,
        )

    # 计算需要省略的总行数
    omit_total = total_lines - max_lines
    result_lines = truncated_lines[:max_lines]
    return TruncateResult(
        result="\n".join(result_lines),
        is_omit=True,
        total_line_count=total_lines,
        omit_line_count=omit_total,
        is_line_truncted=is_line_truncted,
    )


def truncate_line(line: str) -> tuple:
    max_length = config.truncate.line_length_limit
    """截断单行，返回(处理后的行, 是否被截断)"""
    if len(line) <= max_length:
        return (False, line)

    keep_len = max_length - 15  # 保留15字符给截断标记
    return (True, f"{line[:keep_len]}[...截断]")


def _filter_line(line) -> bool:
    return get_filter().filter(line)

