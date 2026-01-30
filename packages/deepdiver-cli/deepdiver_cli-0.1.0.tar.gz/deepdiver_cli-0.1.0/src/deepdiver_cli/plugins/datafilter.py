from typing import Protocol


class DataFilter(Protocol):
    """
    数据过滤接口：str → bool
    """

    def filter(self, raw: str) -> bool:
        raise NotImplementedError


class NoOpFilter:
    """
    空实现：不过滤
    """

    def filter(self, raw: str) -> bool:
        return False
