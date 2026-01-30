from typing import override
from pydantic import Field
from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet


class FinishInput(ToolInput):
    status: str = Field(description="任务状态，success/failure")


class FinishTool(BaseTool[FinishInput]):
    """
    无论诊断类问题，还是非诊断类问题，在准备输出最终结论或回复前，先调用此工具，标记任务完成
    """

    name = "Finish"
    description = "无论诊断类问题，还是非诊断类问题，在准备输出最终结论或回复前，先调用此工具，标记任务完成"
    params = FinishInput

    @override
    async def __call__(self, params):
        return ToolRet(success=True, summary="Success")
