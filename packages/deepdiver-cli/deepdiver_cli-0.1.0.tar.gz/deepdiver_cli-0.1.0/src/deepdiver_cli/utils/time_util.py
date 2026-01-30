import re


def is_time_format(time: str) -> bool:
    return re.search(r"(\d{2}:\d{2}:\d{2})", time) is not None
