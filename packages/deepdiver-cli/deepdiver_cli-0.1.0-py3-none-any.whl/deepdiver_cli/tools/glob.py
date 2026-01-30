import asyncio
import pathlib
from typing import List, Optional, Set, override

from pydantic import Field

from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet, ToolError
from deepdiver_cli.utils.file_util import is_within_dirs


class GlobInput(ToolInput):
    root_dir: str = Field(description="要探索的根目录绝对路径或相对路径。")
    patterns: Optional[List[str]] = Field(
        default=[],
        description=(
            "glob 模式数组（相对于 root），例如 ['**/*.log', '**/*.trace']。"
            "若为 None 或空，则默认使用 ['**/*']。"
        ),
    )
    max_depth: Optional[int] = Field(
        default=3,
        description=(
            "最大递归深度。根目录为深度 0，1 表示只遍历一层子目录。"
            "若为 None，则不限制递归深度。"
        ),
    )
    include_hidden: Optional[bool] = Field(
        default=False,
        description="是否包含隐藏文件和隐藏目录（以点号开头）。默认 false。",
    )


class GlobTool(BaseTool[GlobInput]):
    name = "Glob"
    description = (
        "通用目录探索工具，基于 glob 模式遍历目录，帮助了解一个目录下有哪些文件/子目录，"
        "常用于问题目录或日志目录初探。"
    )
    params = GlobInput
    timeout_s = 8.0

    def __init__(self, allow_dirs: Set[str]):
        super().__init__()
        self.allow_dirs = allow_dirs

    @override
    async def __call__(self, params) -> ToolRet:
        # 校验pattern
        if params.patterns:
            for pattern in params.patterns:
                if pattern == "." or pattern == "..":
                    return ToolRet(
                        success=False, summary="Pattern `.` or `..` is not allowed!"
                    )

        # 检查是否允许访问
        if not is_within_dirs(params.root_dir, self.allow_dirs):
            return ToolRet(
                success=False,
                summary=f"Access denied: `root` must be within {self.allow_dirs}",
            )

        root_path = pathlib.Path(params.root_dir)
        # 基础校验
        if not root_path.exists():
            return ToolRet(success=False, summary="Directory is not found")
        if not root_path.is_dir():
            return ToolRet(success=False, summary="Given root is not a directory")

        patterns = params.patterns or ["**/*"]
        max_depth = params.max_depth
        include_hidden = params.include_hidden

        def is_hidden(p: pathlib.Path) -> bool:
            # 任一路径组件以 '.' 开头即认为是隐藏
            for part in p.parts:
                if part.startswith("."):
                    return True
            return False

        def depth_ok(p: pathlib.Path) -> bool:
            if max_depth is None:
                return True
            # root 深度为 0，子路径深度为其相对路径组件数
            try:
                rel = p.relative_to(root_path)
            except ValueError:
                # 不在 root 之下，防御性处理：直接过滤
                return False
            depth = len(rel.parts)
            return depth <= max_depth

        def walk() -> set:
            results = set()

            try:
                for pattern in patterns:
                    # 使用 rglob 实现 pattern 匹配
                    for p in root_path.rglob(pattern):
                        if not depth_ok(p):
                            continue
                        if not include_hidden and is_hidden(p.relative_to(root_path)):
                            continue
                        # 只输出相对路径
                        rel_str = str(p.relative_to(root_path))
                        results.add(rel_str)
            except PermissionError as e:
                raise ValueError("Directory Access denied") from e
            except Exception as e:
                raise ValueError(f"Glob error: {e!r}") from e

            if not results:
                return set()  # 没有匹配项时返回空字符串，由上层决定如何解释

            # 统一排序输出，便于阅读和测试
            return set(sorted(results))

        try:
            loop = asyncio.get_running_loop()
            paths = await asyncio.wait_for(
                loop.run_in_executor(None, walk),
                timeout=self.timeout_s,
            )
        except asyncio.TimeoutError as e:
            raise ToolError("Glob timed out") from e

        path_str = "\n".join(paths) if paths else ""
        trunck_path_str = "\n".join(list(paths))[:5] if len(paths) > 5 else path_str
        return ToolRet(
            success=True,
            summary=f"{len(paths)} paths",
            data={"paths": path_str, "count": len(paths), "depth": max_depth},
            human_readable_content=f"Found {len(paths)} path(s):\n{trunck_path_str}",
        )
