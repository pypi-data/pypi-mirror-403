from __future__ import annotations
import datetime
import re
from deepdiver_cli.config import config
from deepdiver_cli.utils.file_util import read_text
from deepdiver_cli.utils.timezone import now_local

# 分析Agent提示语文件
main_agent_prompt_file = config.prompt_dir / "deepdiver.md"

# knowledge_config文件
knowledge_config_file = config.config_dir / "knowledge_config.toml"


date_placeholder = "{{current_date}}"
support_knowledge_placeholder = "{{support_knowledge}}"


def system_prompt() -> str:
    """
    生成系统提示
    """
    prompt = read_text(main_agent_prompt_file)

    if not prompt:
        raise ValueError("System prompt is empty")

    # date
    def current_date(m):
        return now_local().strftime("%Y-%m-%d")

    prompt = re.sub(date_placeholder, current_date, prompt)

    # support_knowledge
    def support_knowledge(m):
        return read_text(knowledge_config_file)

    prompt = re.sub(support_knowledge_placeholder, support_knowledge, prompt)
    return prompt
