import os
import asyncio
from typing import Optional, Set, override
from pathlib import Path

from pydantic import Field
from deepdiver_cli.react_core.tool import BaseTool, ToolError, ToolInput, ToolRet
from deepdiver_cli.utils.file_util import is_within_dirs
from deepdiver_cli.app.processor import get_desensitizer
from deepdiver_cli.utils.truncate_util import truncate_line


class ReadInput(ToolInput):
    """读取工具的输入参数模型"""

    file_path: str = Field(description="文件绝对或相对路径")
    offset: Optional[int] = Field(
        default=0,
        description="起始行数，默认0",
    )
    limit: Optional[int] = Field(
        default=100,
        description="读取的行数，不填则使用默认值（默认100，最大300）",
    )


class ReadTool(BaseTool[ReadInput]):
    """
    安全文件读取工具，支持分页读取大文件
    核心安全特性：
    - 路径遍历攻击防护
    - 符号链接解析校验
    - 工作目录边界限制
    - 隐藏文件过滤
    """

    name = "Read"
    description = """读取任意文件。- 适用场景：
            - 完整异常堆栈可读取（例如已经从Grep得到了异常事件在日志中的行数，需要进一步查看完整堆栈）
            - 读取配置文件
            - 探测文件格式（必须指定limit）
            - 不适用场景：
            - 可以通过Grep/Inspect快速获取到完整信息的场景
            """
    params = ReadInput
    timeout_s = 20.0  # 文件读取超时时间

    # 安全配置：禁止读取的文件扩展名
    FORBIDDEN_EXTENSIONS = {".db", ".sqlite", ".key", ".pem", ".p12", ".pfx"}
    # 最大单次读取行数
    MAX_LINE = 300

    def _validate_path_security(self, file_path: str) -> Path:
        """
        多层级路径安全校验
        抛出 ToolError 如果校验失败
        """
        try:
            if any(char in file_path for char in ["\0", "\n", "\r", "\t"]):
                raise ToolError("Path contains illegal characters")

            # 3. 解析为绝对路径
            path = Path(file_path)

            # 4. 禁止隐藏文件和系统文件
            if path.name.startswith("."):
                raise ToolError("Hidden files are not allowed")

            # 5. 禁止特定扩展名
            if path.suffix.lower() in self.FORBIDDEN_EXTENSIONS:
                raise ToolError(f"Files with {path.suffix} extension are not allowed")

            abs_path = path.resolve()
            # 7. 工作目录边界检查（核心防护）
            if not is_within_dirs(file_path, self.allow_dirs):
                raise ToolError(f"Access denied: File must be within {self.allow_dirs}")

            # 8. 文件存在性和类型校验
            if not abs_path.exists():
                raise ToolError(f"File does not exist: {abs_path}")

            if not abs_path.is_file():
                raise ToolError(f"Path is not a file: {abs_path}")

            if not os.access(abs_path, os.R_OK):
                raise ToolError(f"File is not readable: {abs_path}")

            return abs_path

        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Path validation unexpected error: {e}") from e

    async def _read_file_async(
        self, file_path: Path, offset: int, limit: Optional[int]
    ) -> str:
        """异步执行文件读取操作"""

        def _read():
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                # 分页读取
                lines = []
                current_line = 0

                # 定位到起始行
                while current_line < offset:
                    if not f.readline():
                        break  # 文件结束
                    current_line += 1

                # 读取指定行数
                lines_read = 0
                while limit is None or lines_read < limit:
                    line = f.readline()
                    if not line:
                        break  # 文件结束
                    current_line += 1
                    # 超长截断
                    (_, truncated_line) = truncate_line(line)
                    lines.append(
                        str(current_line)
                        + ":"
                        + get_desensitizer().mask(truncated_line)
                    )
                    lines_read += 1

                return "".join(lines)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _read)

    def __init__(self, allow_dirs: Set[str]):
        super().__init__()
        self.allow_dirs = allow_dirs

    @override
    async def __call__(self, params) -> ToolRet:
        """主入口：解析输入 → 安全校验 → 异步读取 → 返回结果"""
        file_path_str = params.file_path
        offset = max(0, params.offset or 0)  # 确保非负
        limit = min(ReadTool.MAX_LINE, params.limit or 100)

        if limit is not None:
            limit = max(1, limit)  # 确保正数

        try:
            # 2. 路径安全校验
            safe_path = self._validate_path_security(file_path_str)

            # 3. 异步读取（带超时控制）

            content = await asyncio.wait_for(
                self._read_file_async(safe_path, offset, limit), timeout=self.timeout_s
            )

            lines = content.split("\n")
            line_count = len([line for line in lines if line])

            # 4. 返回成功结果
            return ToolRet(
                success=True,
                summary=f"Read {line_count} lines",
                data={
                    "result": content,
                    "line_count": line_count,
                    "file_size": "{0:.2f} Mb".format(
                        float(safe_path.stat().st_size) / 1024 / 1024
                    ),
                },
                human_readable_content=f"Read {line_count} lines({offset}-{offset + limit})",
            )

        except asyncio.TimeoutError:
            return ToolRet(
                success=False,
                summary=f"Read operation timed out after {self.timeout_s} seconds",
            )
        except ToolError as e:
            return ToolRet(success=False, summary=str(e))
        except UnicodeDecodeError as e:
            return ToolRet(
                success=False, summary=f"File encoding error (utf-8 required): {e}"
            )
        except IOError as e:
            return ToolRet(success=False, summary=f"IO error during read: {e}")
        except Exception as e:
            return ToolRet(success=False, summary=f"Unexpected error: {repr(e)}")
