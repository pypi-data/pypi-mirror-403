import os
from pathlib import Path
import shutil
import tempfile
from typing import Set, override, Optional, TYPE_CHECKING

from pydantic import Field
import structlog

from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.config import config
from deepdiver_cli.app.processor import get_decryptor
from deepdiver_cli.utils.file_util import is_within_dirs

# Avoid circular imports
if TYPE_CHECKING:
    from deepdiver_cli.session import Session

logger = structlog.get_logger(__name__)


class ProcessFileInput(ToolInput):
    path: str = Field(description="带处理文件的绝对路径")
    type: str = Field(description=("文件类型，传文件后缀，没有后缀传空"))


class ProcessFileTool(BaseTool[ProcessFileInput]):
    """
    文件预处理工具：
    - 输入：原始文件路径
    - 功能：按类型对文件进行预处理，例如解密、脱敏、格式归一化等
    - 输出：处理后的文件路径（字符串），供后续 Grep、Inspect 等工具使用
    """

    name = "ProcessFile"
    description = """对单个"原始文件"进行预处理，用于文件解密、脱敏、提取文本、解压缩等场景。
以下文件使用前需要进行处理：
- 日志文件：后缀名为.log、.alog等，或名称暗示是日志的文件
- 非文本文件：例如：压缩包、二进制文件、图片、PDF等
对于源代码无需进行处理。如果不确定是否要处理，可咨询用户"""
    params = ProcessFileInput
    timeout_s = 10.0

    def __init__(
        self,
        allow_dirs: Set[str],
        session: Optional["Session"] = None
    ) -> None:
        super().__init__()
        self.allow_dirs = allow_dirs
        self.session = session

        # Use session's logs_parsed directory if session is available
        if session and hasattr(session, 'logs_parsed_dir'):
            self.output_dir = str(session.logs_parsed_dir)
        else:
            # Fallback: use a temporary directory if no session
            import tempfile
            self.output_dir = tempfile.mkdtemp(prefix="deepdiver_processed_")

        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    @override
    async def __call__(self, params) -> ToolRet:
        if not is_within_dirs(params.path, self.allow_dirs):
            return ToolRet(
                success=False,
                summary=f"Access denied: File must be within {self.allow_dirs}",
            )
        path = Path(params.path)

        if not path.exists():
            return ToolRet(
                success=False,
                summary=f"ProcessFile error: file '{path}' does not exist",
            )
        if not path.is_file():
            return ToolRet(
                success=False, summary=f"ProcessFile error: '{path}' is not a file"
            )
        try:
            path = params.path
            type = params.type
            source_files = [path]
            logger.debug("processfile", source_log_path=path, type=type)
            if source_files:
                temp_dir = tempfile.mkdtemp(prefix="deepdiver_temp_")
                processed_files = []

                for src_path in source_files:
                    filename = os.path.basename(src_path)
                    temp_path = os.path.join(temp_dir, filename)
                    shutil.copy2(src_path, temp_path)
                    self._process_log(processed_files, src_path, temp_path, filename)
                shutil.rmtree(temp_dir)
                return ToolRet(
                    success=True,
                    summary="File processed",
                    data="\n".join(processed_files),
                    human_readable_content=f"File processed :\n{'\n'.join(processed_files)}",
                )
            else:
                return ToolRet(success=True, summary="File is not found")

        except Exception as e:
            return ToolRet(success=False, summary=f"ProcessFile error: {e!r}")

    def _process_log(
        self,
        processed_files: list[str],
        original_path: str,
        temp_path: str,
        filename: str,
    ):
        try:
            decrypted_log_path = get_decryptor().decrypt(
                input_file_path=temp_path,
                output_dir=self.output_dir,
                filename=filename,
            )
            os.remove(temp_path)
            processed_files.append(decrypted_log_path)
        except Exception as e:
            logger.warning(
                "processfile", path=temp_path, msg=f"Decrypt file failed {e}"
            )
            os.remove(temp_path)
            log_path = os.path.join(self.output_dir, filename)
            shutil.copy2(original_path, log_path)
            processed_files.append(log_path)
