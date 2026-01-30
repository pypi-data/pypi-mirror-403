import asyncio
import enum
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Protocol
import time

from pydantic import BaseModel

from deepdiver_cli.logger import logger
from deepdiver_cli.utils.command_runner import CommandRunner
from deepdiver_cli.utils.measure_time import auto_time_unit


def _strip_ansi(s: str) -> str:
    """简单去掉 ANSI 颜色码（避免影响 JSON 解析）"""
    import re

    ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return ansi_re.sub("", s)


class CodeAnalyzerError(Exception):
    """代码分析异常"""

    pass


class OutputFormat(enum.Enum):
    JSON = "json"
    STREAM_JSON = "stream_json"
    TEXT = "text"


class CodeAnalyzeRequest(BaseModel):
    """代码分析请求"""

    session_id: Optional[str]
    """会话id"""
    code_path: Path
    """代码绝对路径"""
    prompt: str
    """分析任务说明"""
    timeout_sec: int = 600
    """超时时间，单位秒"""
    output_format: OutputFormat = OutputFormat.JSON
    """输出格式"""


class CodeAnalyzeResult(BaseModel):
    """代码分析报告"""

    is_success: bool
    """是否成功"""
    session_id: str
    """会话id"""
    analysis: str
    """分析报告"""


class CodeAnalyzer(Protocol):
    async def analyze(self, request: CodeAnalyzeRequest) -> CodeAnalyzeResult:
        raise NotImplementedError()


class ClaudeCodeAnalyzer:
    def __init__(self) -> None:
        self.session_id = ""

    async def analyze(self, request: CodeAnalyzeRequest) -> CodeAnalyzeResult:
        code_path = request.code_path

        if not code_path.is_dir():
            raise CodeAnalyzerError(f"code_path 不存在或不是目录: {str(code_path)}")

        if not code_path.is_absolute():
            raise CodeAnalyzerError(f"code_path 必须是绝对路径: {str(code_path)}")

        cmd = ["claude", "-p"]

        match request.output_format:
            case OutputFormat.JSON:
                cmd += ["--output-format", "json"]
            case OutputFormat.STREAM_JSON:
                cmd += ["--output-format", "stream-json"]
            case _:
                # 不指定--output-format"，默认TEXT格式
                pass

        if request.session_id:
            cmd += ["--resume", self.session_id]

        logger.info("analyze.start", code_path=str(code_path), cmd=" ".join(cmd))

        cmd.append(request.prompt)

        try:
            start_time = time.perf_counter()
            command_runner = CommandRunner(
                cwd=code_path, timeout_sec=request.timeout_sec, env=os.environ.copy()
            )
            completed = await command_runner(cmd)

            logger.info(
                "analyze.finish",
                cost=f"{auto_time_unit(time.perf_counter() - start_time)}",
            )
        except asyncio.TimeoutError as e:
            raise CodeAnalyzerError(
                f"调用 Claude CLI 超时（>{request.timeout_sec}s）"
            ) from e
        except FileNotFoundError as e:
            raise CodeAnalyzerError(
                "找不到 `claude` 命令，请确认已安装并在 PATH 中"
            ) from e

        if completed.returncode != 0:
            # stderr 里可能有有用信息，可以打日志
            raise CodeAnalyzerError(
                f"Claude CLI 退出码非 0: {completed.returncode}, stderr: {completed.stderr}"
            )

        raw_out = completed.stdout
        if not raw_out.strip():
            raise CodeAnalyzerError("claude CLI 没有产生任何输出")

        # 去掉 ANSI 颜色码，避免影响后续解析
        clean_out = _strip_ansi(raw_out)

        match request.output_format:
            case OutputFormat.JSON:
                return _JsonResultParser().parse(clean_out)
            case OutputFormat.STREAM_JSON:
                raise NotImplementedError()
            case _:
                return _TextResultParser().parse(clean_out)


class _TextResultParser:
    def parse(self, result_text: str) -> CodeAnalyzeResult:
        return CodeAnalyzeResult(is_success=True, session_id="", analysis=result_text)


class _JsonResultParser:
    def parse(self, result_json: str) -> CodeAnalyzeResult:
        try:
            result_dict = json.loads(result_json)
            (is_success, session_id, analysis, usage) = self._extra_data(result_dict)
            return CodeAnalyzeResult(
                is_success=is_success, session_id=session_id, analysis=analysis
            )
        except json.JSONDecodeError as e:
            logger.error("analyze.loadjson.failed", json=result_dict)
            raise CodeAnalyzerError(f"JSON 解析失败: {e}") from e

    def _extra_data(self, result_dict: Dict[str, Any]) -> tuple[bool, str, str, dict]:
        """解析 is_error/session_id/result/usage"""
        is_success = not result_dict.get("is_error", True)

        session_id = result_dict.get("session_id", "")

        result = result_dict.get("result", "")

        usage = result_dict.get("usage", {})

        logger.info(
            "analyze.parsejson",
            session_id=session_id,
            is_success=is_success,
            usage=usage,
        )
        return is_success, session_id, result, usage
