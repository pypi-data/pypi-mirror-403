import asyncio
import sys
from pydantic import Field
from typing import override

from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet


class AskHumanInput(ToolInput):
    question: str = Field(
        description="要向用户提出的问题，需简洁明确。", min_length=1, max_length=2000
    )


class AskHumanTool(BaseTool[AskHumanInput]):
    name = "AskHuman"
    description = "向用户请求补充/确认关键信息。"
    params = AskHumanInput
    timeout_s = 3600  # 设置一个极大的超时（1小时），确保不会意外超时

    @override
    async def __call__(self, params) -> ToolRet:
        question = params.question.strip()

        if not question:
            return ToolRet(success=False, summary="Error: Question cannot be empty")

        # 在终端打印问题
        print(f"\n{'=' * 60}")
        print("🙋 Agent需要你的输入:")
        print(f"   {question}")
        print(f"{'=' * 60}\n")
        print("请输入您的回答（按回车提交）: ", end="", flush=True)

        # 将阻塞式input()调用放到线程池中，避免阻塞整个事件循环
        loop = asyncio.get_running_loop()

        def _read_from_terminal() -> str:
            """同步函数：从终端读取一行输入"""
            try:
                return sys.stdin.readline().strip()
            except EOFError:
                # Ctrl+D
                raise RuntimeError("用户输入被中断 (EOF)")
            except KeyboardInterrupt:
                # Ctrl+C
                raise RuntimeError("用户输入被中断 (KeyboardInterrupt)")
            except Exception as e:
                raise RuntimeError(f"读取输入失败: {e}")

        try:
            user_response = await asyncio.wait_for(
                loop.run_in_executor(None, _read_from_terminal), timeout=self.timeout_s
            )

            if not user_response:
                return ToolRet(
                    success=True,
                    summary="User has no additional information",
                )

            return ToolRet(
                success=True,
                summary="User has replied.",
                data=user_response,
                human_readable_content=user_response,
            )

        except asyncio.TimeoutError:
            return ToolRet(success=False, summary="Error: User input timed out")
        except RuntimeError as e:
            return ToolRet(success=False, summary=f"Error: {e}")
        except Exception as e:
            return ToolRet(
                success=False, summary=f"Unexpected error: {type(e).__name__}: {str(e)}"
            )
