import os
from pathlib import Path
from typing import List, Optional, override
from pydantic import Field
from deepdiver_cli.config import config
from deepdiver_cli.chat.chat_model import (
    LLMMessage,
    make_sys_message,
    make_user_message,
)
from deepdiver_cli.react_core.llm import LLMClient
from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
import structlog
from deepdiver_cli.utils.file_util import read_text
from deepdiver_cli.utils.xml import extract_tag_content

logger = structlog.get_logger(__name__)

# llm
REVIEW_EVIDENCE_PROMPT_FILE = (config.prompt_dir / "reviewer.md").resolve()
# user input placeholder
ISSUE_PLACE_HOLDER = "{{issue}}"
TIMELINE_PLACE_HOLDER = "{{timeline}}"
EVIDENCE_PLACE_HOLDER = "{{evidence}}"
KNOWLEDGE_BASIS_PLACE_HOLDER = "{{knowledge_basis}}"
LOG_BASIS_PLACE_HOLDER = "{{log_basis}}"
CODE_BASIS_PLACE_HOLDER = "{{code_basis}}"
OTHER_BASIS_PLACE_HOLDER = "{{other_basis}}"
CONCLUSION_PLACE_HOLDER = "{{conclusion}}"
# system prompt placeholder
KNOWLEDGE_DIR = config.knowledge_dir
USER_INPUT_TEMPLATE_FILE = (config.prompt_dir / "review_template.md").resolve()
KNOWLEDGE_PLACE_HOLDER = "{{knowledge}}"
COMMIT_COUNT_PLACE_HOLDER = "{{commit_count}}"
MAX_COMMIT_COUNT_PLACE_HOLDER = "{{max_commit_count}}"
report_header = "report_header"
report_conclusion = "report_conclusion"


class ReviewInput(ToolInput):
    path: str = Field(description="当前主要分析使用的日志文件路径。")
    issue: str = Field(description="用户问题的完整描述。")
    ref_knowledge_keys: list[str] = Field(
        description="当前引用的知识类型 key 列表，例如：Login。"
    )
    timeline_event: str = Field(
        description="当前完整的事件时间轴总结，格式采用【时间轴】模版格式"
    )
    evidence_chain: str = Field(description="当前的证据链，格式采用【证据链】模版格式")
    knowledge_evidence: str = Field(
        description="支持当前证据链和结论的知识库、技术常识依据。"
    )
    log_evidence: str = Field(
        description="支持当前证据链和结论的关键日志依据（时间+事件），所有证据链中引用的事件都要列举"
    )
    code_analysis_evidence: Optional[str] = Field(
        default="无", description="代码分析的关键证据"
    )
    other_basis: Optional[str] = Field(default="无", description="其他依据")
    conclusion: str = Field(description="你当前的结论。")


class ReviewTool(BaseTool[ReviewInput]):
    name = "Review"
    description = "请求专家评审当前的证据链与现阶段结论。"
    params = ReviewInput

    def __init__(self) -> None:
        super().__init__()
        self.review_config = config.tools.review
        self.llm = LLMClient(self.review_config.llm)
        self.current_commit_count = 0

    @override
    async def __call__(self, params):
        self.current_commit_count += 1
        report = await self._review_evidence(params)

        return ToolRet(
            success=True,
            summary="Review completed",
            data=report,
            human_readable_content=f"{extract_tag_content(report, report_header)[0]}\n{extract_tag_content(report, report_conclusion)[0]}",
        )

    async def _review_evidence(self, params: ReviewInput) -> str:
        """
        review evidence
        """
        logger.info("llm.reviewevidence.start", commit_count=self.current_commit_count)
        evidence = self._build_evidence(params)
        print("\n" + "=" * 20 + "提交证据" + "=" * 20 + "\n")
        print(evidence)
        trajectory_msgs: List[LLMMessage] = []
        trajectory_msgs.append(make_sys_message(self._get_sys_prompt(params)))
        trajectory_msgs.append(make_user_message(evidence))
        rsp = await self.llm.step(messages=trajectory_msgs)
        return rsp.content

    def _build_evidence(self, params: ReviewInput) -> str:
        user_input_template: str = read_text(USER_INPUT_TEMPLATE_FILE)
        res = (
            user_input_template.replace(ISSUE_PLACE_HOLDER, params.issue)
            .replace(KNOWLEDGE_BASIS_PLACE_HOLDER, params.knowledge_evidence)
            .replace(LOG_BASIS_PLACE_HOLDER, params.log_evidence)
            .replace(TIMELINE_PLACE_HOLDER, params.timeline_event)
            .replace(EVIDENCE_PLACE_HOLDER, params.evidence_chain)
            .replace(CODE_BASIS_PLACE_HOLDER, params.code_analysis_evidence or "")
            .replace(OTHER_BASIS_PLACE_HOLDER, params.other_basis or "")
            .replace(CONCLUSION_PLACE_HOLDER, params.conclusion)
        )
        return res

    def _get_sys_prompt(self, input: ReviewInput) -> str:
        system_prompt: str = read_text(REVIEW_EVIDENCE_PROMPT_FILE)
        if not system_prompt:
            raise ValueError("System prompt is empty")
        key_to_path = [
            (key, self._validate_path_safety(key)) for key in input.ref_knowledge_keys
        ]
        knowledge_list = [
            f"<{key}Knowledge>\n{read_text(path)}\n</{key}Knowledge>"
            for (key, path) in key_to_path
        ]
        knowledges = "\n".join(knowledge_list)
        prompt = (
            system_prompt.replace(KNOWLEDGE_PLACE_HOLDER, knowledges)
            .replace(COMMIT_COUNT_PLACE_HOLDER, str(self.current_commit_count))
            .replace(
                MAX_COMMIT_COUNT_PLACE_HOLDER, str(self.review_config.max_commit_count)
            )
        )
        return prompt

    def _validate_path_safety(self, knowledge_key: str) -> Path:
        """
        防止路径遍历攻击，确保文件在KNOWLEDGE_DIR内
        """
        # 构建安全文件名：只能包含允许的字符
        safe_filename = f"{knowledge_key}.md"

        # 规范化路径并检查是否在知识库目录内
        try:
            # 使用commonpath检查防止目录遍历
            target_path = (KNOWLEDGE_DIR / safe_filename).resolve()
            if os.path.commonpath([target_path, KNOWLEDGE_DIR]) != str(KNOWLEDGE_DIR):
                raise ValueError(f"非法路径访问: {knowledge_key}")

            return target_path
        except Exception as e:
            raise ValueError(f"路径验证失败: {e}")
