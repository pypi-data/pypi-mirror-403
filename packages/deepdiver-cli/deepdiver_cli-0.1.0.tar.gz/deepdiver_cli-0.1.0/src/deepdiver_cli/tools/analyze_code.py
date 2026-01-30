from pathlib import Path
from typing import Set, override
from pydantic import Field

from deepdiver_cli.config import config
from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.tools.analyze_code_impl import (
    CodeAnalyzeRequest,
    CodeAnalyzer,
    CodeAnalyzerError,
    ClaudeCodeAnalyzer,
)
from deepdiver_cli.utils.file_util import is_within_dirs, read_text
from deepdiver_cli.utils.xml import extract_tag_content


class AnalyzeCodeInput(ToolInput):
    instructions: str = Field(
        description=read_text(Path(__file__).parent / "analyze_code.md")
    )
    code_path: str = Field(description="单个代码目录的绝对路径，来自任务输入")


class AnalyzeCodeTool(BaseTool[AnalyzeCodeInput]):
    name = "AnalyzeCode"
    description = """在日志或知识不足时，请求专家分析项目代码以补充证据。

**重要使用前提**：
1. 在调用此工具之前，必须先调用 ask_human 工具征求用户同意
2. 向用户说明需要分析的代码路径（code_path）
3. 提供明确的 yes/no 选项让用户确认
4. 只有当用户明确回复 "yes" 或 "y" 时，才能调用此工具进行代码分析

如果用户回复 "no" 或 "n"或未提供额外信息，则不应调用此工具，应尝试其他分析方式。"""
    params = AnalyzeCodeInput

    def __init__(
        self,
        allow_dirs: Set[str],
    ) -> None:
        super().__init__()
        self.allow_dirs = allow_dirs
        self.prompt_path = config.prompt_dir / "code_analyzer.md"
        self.analyzer: CodeAnalyzer = ClaudeCodeAnalyzer()

    def _get_prompt(self, instructions: str) -> str:
        prompt = read_text(self.prompt_path)
        return prompt.replace("{{analyze_instructions}}", instructions)

    @override
    async def __call__(self, params) -> ToolRet:
        if not params.code_path:
            return ToolRet(success=False, summary="`code_path` is required")

        if not is_within_dirs(params.code_path, self.allow_dirs):
            return ToolRet(
                success=False,
                summary=f"Access denied: `code_path` must be one of {self.allow_dirs}",
            )

        print("\n" + "=" * 20 + "分析代码" + "=" * 20 + "\n")
        print(f"code_path:\n{params.code_path}\n")
        print(f"instructions:\n{params.instructions}\n")
        try:
            analyze_result = await self.analyzer.analyze(
                CodeAnalyzeRequest(
                    session_id="",
                    code_path=Path(params.code_path),
                    prompt=self._get_prompt(params.instructions),
                )
            )
            if not analyze_result.is_success:
                return ToolRet(
                    success=False,
                    summary="Analyze failed, analyze tool error, please retry",
                )

            if not analyze_result.analysis:
                return ToolRet(
                    success=False,
                    summary="Analyze failed, analyze tool return empty result, please retry",
                )
            conclusions = extract_tag_content(analyze_result.analysis, "conclusion")

            return ToolRet(
                success=True,
                data=analyze_result.analysis,
                human_readable_content=conclusions[0] if conclusions else "",
            )
        except CodeAnalyzerError as e:
            raise
            # logger.error("toolcalling.failed", msg=f"{e!r}")
            # return ToolRet(success=False, summary=f"Analyze failed:{e!r}")
