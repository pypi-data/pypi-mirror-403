import os
import asyncio
from typing import override
from pathlib import Path
from pydantic import Field

from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.config import config


class LoadKnowledgeInput(ToolInput):
    knowledge_key: str = Field(
        description="知识库类型标识，例如：Login",
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$",  # 只允许字母数字下划线
    )


class LoadKnowledgeTool(BaseTool[LoadKnowledgeInput]):
    name = "LoadKnowledge"
    description = "加载与问题相关的诊断知识库。"
    params = LoadKnowledgeInput
    timeout_s = 2.0

    def _validate_path_safety(self, knowledge_key: str) -> Path:
        """
        防止路径遍历攻击，确保文件在KNOWLEDGE_DIR内
        """
        # 构建安全文件名：只能包含允许的字符
        safe_filename = f"{knowledge_key}.md"

        # 规范化路径并检查是否在知识库目录内
        try:
            # 使用commonpath检查防止目录遍历
            target_path = (self.knowledge_dir / safe_filename).resolve()
            if os.path.commonpath([target_path, self.knowledge_dir]) != str(
                self.knowledge_dir
            ):
                raise ValueError(f"非法路径访问: {knowledge_key}")

            return target_path
        except Exception as e:
            raise ValueError(f"路径验证失败: {e}")

    def __init__(self):
        super().__init__()
        self.knowledge_dir = config.knowledge_dir

    @override
    async def __call__(self, params) -> ToolRet:
        """异步加载知识文件，返回原始Markdown内容"""
        knowledge_key = params.knowledge_key.strip()

        try:
            # 1. 路径安全检查
            knowledge_file = self._validate_path_safety(knowledge_key)

            # 2. 异步读取文件（避免阻塞事件循环）
            loop = asyncio.get_running_loop()

            # 使用run_in_executor避免阻塞
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None, self._load_knowledge, knowledge_file, knowledge_key
                ),
                timeout=self.timeout_s,
            )

            return result

        except asyncio.TimeoutError:
            return ToolRet(
                success=False,
                summary="Knowledge loading timed",
                error={
                    "status": "timeout",
                    "knowledge_key": knowledge_key,
                    "error_message": f"Knowledge loading timed out after {self.timeout_s}s",
                },
            )
        except ValueError as e:
            # 路径验证失败
            return ToolRet(
                success=False,
                summary="Path check failed",
                error={
                    "status": "security_error",
                    "knowledge_key": knowledge_key,
                    "msg": f"{e!r}",
                },
            )
        except Exception as e:
            # 其他意外错误
            return ToolRet(
                success=False,
                summary="Unexpected error happened",
                error={
                    "status": "unexpected_error",
                    "knowledge_key": knowledge_key,
                    "msg": f"{e!r}",
                },
            )

    def _load_knowledge(self, knowledge_file: Path, knowledge_key: str) -> ToolRet:
        if not knowledge_file.exists():
            return ToolRet(
                success=False,
                summary="Knowledge file not found",
                error={
                    "status": "file_not_exists",
                    "knowledge_key": knowledge_key,
                    "msg": f"Knowledge file not found: {knowledge_file.name}",
                },
            )

        # 正常读取文件
        knowledge_content = knowledge_file.read_text(encoding="utf-8")
        truncated_content = (
            f"{knowledge_content[:50]}\n..." if len(knowledge_content) > 50 else knowledge_content
        )
        return ToolRet(
            success=True,
            summary="Knowledge is loaded",
            data={
                "knowledge_key": knowledge_key,
                "knowledge_content": knowledge_content,
                "file_path": str(knowledge_file),
            },
            human_readable_content=truncated_content,
        )
