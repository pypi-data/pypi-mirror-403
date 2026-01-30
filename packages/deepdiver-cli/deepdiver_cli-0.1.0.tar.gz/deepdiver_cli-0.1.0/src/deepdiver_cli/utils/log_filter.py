from dataclasses import dataclass
import re


@dataclass
class TimeFilterResult:
    content: str
    """过滤结果"""
    content_start_time: str = ""
    """实际的开始时间"""
    content_end_time: str = ""
    """实际的结束时间"""


def apply_time_filter(content: str, time_range: tuple[str, str]) -> TimeFilterResult:
    """基于时间范围过滤结果"""
    if not content:
        return TimeFilterResult(content)
    if not time_range:
        return TimeFilterResult(content)

    if len(time_range) != 2:
        return TimeFilterResult(content)
    start_str = time_range[0]
    end_str = time_range[1]

    filtered_lines = []
    content_start_time = ""
    content_end_time = ""
    for line in content.split("\n"):
        # 匹配时间格式: HH:mm:ss
        time_match = re.search(r"(\d{2}:\d{2}:\d{2})", line)
        if time_match and not content_end_time:
            content_start_time = time_match.group(1)
        if time_match:
            content_end_time = time_match.group(1)
        if time_match and start_str <= time_match.group(1) <= end_str:
            filtered_lines.append(line)

    return TimeFilterResult(
        content="\n".join(filtered_lines),
        content_start_time=content_start_time,
        content_end_time=content_end_time,
    )


if __name__ == "__main__":
    print(
        apply_time_filter(
            "12:00:00.123 ddd ddd\n12:00:01.123 ddd ddd\n12:00:02.123 nnn ddd ",
            ("12:00:01", "12:00:03"),
        )
    )
    pass
