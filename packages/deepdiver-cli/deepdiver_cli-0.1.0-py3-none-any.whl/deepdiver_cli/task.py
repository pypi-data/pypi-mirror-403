from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class WorkDirType(Enum):
    CODE = "code"
    ATTACHMENT = "attachment"


class TaskInput(BaseModel):
    """任务输入"""

    description: str
    """任务描述"""
    code_roots: List[str]
    """代码目录列表"""
    attachment_roots: List[str]
    """附件目录列表（日志、dump、Jira 附件等）"""
    work_dir: str
    """工作目录"""
    work_dir_type: WorkDirType
    """工作目录类型"""


class Runtime(BaseModel):
    model: Optional[str] = ""
