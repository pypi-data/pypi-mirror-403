import asyncio
from dataclasses import dataclass
import shutil
from typing import List, Literal, Optional, Union

from deepdiver_cli.utils.command_runner import CommandRunner


def is_install_ripgrep() -> bool:
    """快速检查ripgrep是否可用"""
    return shutil.which("rg") is not None


@dataclass
class SearchResult:
    success: bool
    content: Optional[str]


class SearchCmdBuilder:
    """
    独立的 ripgrep (rg) 命令构建器

    默认配置：
    - 使用 PCRE2 正则引擎 (-P)
    - 显示行号 (--line-number)
    - 禁用颜色输出 (--color never)
    """

    def __init__(self, pattern: str):
        """初始化构建器，应用默认配置"""
        self._pattern = pattern
        self._paths: List[str] = []
        self._glob: List[str] = []
        self._ignore_case: bool = False
        self._case_sensitive: bool = False
        self._context: Optional[int] = None
        self._before_context: Optional[int] = None
        self._after_context: Optional[int] = None
        self._max_count: Optional[int] = None
        self._pcre2: bool = True  # -P
        self._line_number: bool = True  # --line-number
        self._color: Literal["never", "auto", "always"] = "never"  # --color never

    def pattern(self, pattern: str) -> "SearchCmdBuilder":
        self._pattern = pattern
        return self

    def paths(self, paths: Union[str, List[str]]) -> "SearchCmdBuilder":
        if isinstance(paths, str):
            self._paths = [paths]
        else:
            self._paths = paths
        return self

    def glob(self, patterns: Union[str, List[str]]) -> "SearchCmdBuilder":
        if isinstance(patterns, str):
            self._glob.append(patterns)
        else:
            self._glob.extend(patterns)
        return self

    def ignore_case(self, enable: bool = True) -> "SearchCmdBuilder":
        self._ignore_case = enable
        if enable:
            self._case_sensitive = False
        return self

    def case_sensitive(self, enable: bool = True) -> "SearchCmdBuilder":
        self._case_sensitive = enable
        if enable:
            self._ignore_case = False
        return self

    def context(self, lines: int) -> "SearchCmdBuilder":
        self._context = lines
        return self

    def before_context(self, lines: int) -> "SearchCmdBuilder":
        self._before_context = lines
        return self

    def after_context(self, lines: int) -> "SearchCmdBuilder":
        self._after_context = lines
        return self

    def max_count(self, count: int) -> "SearchCmdBuilder":
        self._max_count = count
        return self

    def pcre2(self, enable: bool = True) -> "SearchCmdBuilder":
        """
        设置是否使用 PCRE2 正则引擎

        Args:
            enable: True 启用 PCRE2 (默认), False 使用默认正则引擎
        """
        self._pcre2 = enable
        return self

    def line_number(self, enable: bool = True) -> "SearchCmdBuilder":
        """
        设置是否显示行号

        Args:
            enable: True 显示行号 (默认), False 隐藏行号
        """
        self._line_number = enable
        return self

    def color(
        self, mode: Literal["never", "auto", "always"] = "never"
    ) -> "SearchCmdBuilder":
        """
        设置颜色输出模式

        Args:
            mode: "never" (默认) 禁用颜色, "auto" 自动检测, "always" 总是启用
        """
        self._color = mode
        return self

    # ==================== 命令构建方法 ====================

    def _validate(self) -> None:
        """验证参数有效性"""

        if self._ignore_case and self._case_sensitive:
            raise ValueError("ignore_case 和 case_sensitive 不能同时为 True")

        context_params = {
            "context": self._context,
            "before_context": self._before_context,
            "after_context": self._after_context,
        }

        for name, value in context_params.items():
            if value is not None and value < 0:
                raise ValueError(f"{name} 不能为负数")

        if self._max_count is not None and self._max_count <= 0:
            raise ValueError("max_count 必须为正整数")

    def build(self) -> List[str]:
        """构建 ripgrep 命令参数列表"""
        self._validate()

        cmd = ["rg"]

        # 默认配置：PCRE2 引擎
        if self._pcre2:
            cmd.append("-P")

        # 默认配置：显示行号
        if self._line_number:
            cmd.append("--line-number")

        # 默认配置：禁用颜色输出
        if self._color != "auto":  # "auto" 是 ripgrep 的默认值，可省略
            cmd.extend(["--color", self._color])

        # 原有选项
        if self._ignore_case:
            cmd.append("-i")
        elif self._case_sensitive:
            cmd.append("-s")

        for pattern in self._glob:
            cmd.extend(["-g", pattern])

        if self._context is not None:
            cmd.extend(["-C", str(self._context)])

        if self._before_context is not None:
            cmd.extend(["-B", str(self._before_context)])

        if self._after_context is not None:
            cmd.extend(["-A", str(self._after_context)])

        if self._max_count is not None:
            cmd.extend(["-m", str(self._max_count)])

        cmd.append(self._pattern)
        cmd.extend(self._paths)

        return cmd

    def build_command_string(self, quote: bool = False) -> str:
        """
        构建命令字符串

        Args:
            quote: 是否使用单引号对含特殊字符的参数进行引用
        """
        cmd_list = self.build()

        if not quote:
            return " ".join(cmd_list)

        parts = []
        for arg in cmd_list:
            if " " in arg or "\t" in arg or "\n" in arg:
                escaped = arg.replace("'", "'\\''")
                parts.append(f"'{escaped}'")
            else:
                parts.append(arg)

        return " ".join(parts)

    def __str__(self) -> str:
        """返回命令字符串表示（默认不使用引号）"""
        return self.build_command_string(quote=False)

    def __repr__(self) -> str:
        """返回对象的可读表示"""
        return f"<RgCommandBuilder pattern='{self._pattern}' paths={self._paths}>"


class Rg:
    def __init__(self, cwd: Optional[str] = None, timeout_sec: int = 60):
        self.cmd_runner = CommandRunner(cwd=cwd, timeout_sec=timeout_sec)

    async def search(self, cmd: List[str]) -> SearchResult:
        try:
            complete = await self.cmd_runner(cmd)
        except FileNotFoundError:
            return SearchResult(
                success=False,
                content="Grep error: 'rg' (ripgrep) not found in PATH",
            )
        except asyncio.TimeoutError as e:
            return SearchResult(success=False, content=f"Grep timeout: {e!r}")
        except Exception as e:
            return SearchResult(success=False, content=f"Grep error: {e!r}")

        # ripgrep 约定：
        # - 0: 有匹配且正常结束
        # - 1: 无匹配
        # - 2: 错误
        if complete.returncode == 0:
            return SearchResult(success=True, content=complete.stdout)
        elif complete.returncode == 1:
            # 无匹配也视为正常，只是结果为空
            return SearchResult(success=True, content=complete.stdout or "")
        else:
            msg = (
                complete.stderr.strip() or f"rg exited with code {complete.returncode}"
            )
            return SearchResult(success=False, content=f"Grep error: {msg}")
