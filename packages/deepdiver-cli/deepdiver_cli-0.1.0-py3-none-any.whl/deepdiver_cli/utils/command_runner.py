import asyncio
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Union


class AsyncCompletedProcess:
    """模拟 subprocess.CompletedProcess 的异步版本"""

    def __init__(
        self,
        args: Union[List[str], str],
        returncode: Optional[int],
        stdout: str,
        stderr: str,
    ) -> None:
        self.args: Union[List[str], str] = args
        self.returncode: Optional[int] = returncode
        self.stdout: str = stdout
        self.stderr: str = stderr

    def check_returncode(self) -> None:
        """如果 returncode 非零，则抛出 CalledProcessError"""
        if self.returncode is None:
            raise RuntimeError("进程尚未完成，returncode 为 None")
        if self.returncode != 0:
            raise subprocess.CalledProcessError(
                self.returncode, self.args, self.stdout, self.stderr
            )

    def __repr__(self) -> str:
        return f"AsyncCompletedProcess(args={self.args}, returncode={self.returncode})"


class CommandRunner:
    """异步命令执行器，封装 subprocess 的异步调用"""

    def __init__(
        self,
        cwd: Union[str, Path, None],
        timeout_sec: Optional[float] = None,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Args:
            cwd: 命令执行的工作目录（current working directory）
            timeout_sec: 默认超时时间（秒），None 表示无超时
            env: 环境变量字典，None 则继承当前环境
        """
        self.cwd: Union[str, None] = str(cwd) if isinstance(cwd, Path) else cwd
        self.timeout_sec: Optional[float] = timeout_sec
        self.env: dict[str, str] = env if env is not None else os.environ.copy()

    async def run(self, cmd: List[str]) -> AsyncCompletedProcess:
        """执行命令并返回结果

        Args:
            cmd: 命令列表，例如 ['python', 'script.py']

        Returns:
            AsyncCompletedProcess: 包含执行结果的对象

        Raises:
            asyncio.TimeoutError: 当命令执行超时时
            RuntimeError: 当进程完成后 returncode 仍为 None 时
        """
        # 创建子进程
        process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )

        try:
            # 等待进程完成，带超时
            stdout: bytes
            stderr: bytes
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_sec
            )

            # 解码输出
            stdout_text: str = stdout.decode("utf-8") if stdout else ""
            stderr_text: str = stderr.decode("utf-8") if stderr else ""

            # 关键检查：确保 returncode 不为 None
            if process.returncode is None:
                process.kill()
                await process.wait()
                raise RuntimeError(f"进程 {cmd} 已完成但 returncode 为 None")

            # 返回封装后的结果对象
            return AsyncCompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
            )

        except asyncio.TimeoutError:
            # 超时则终止进程
            process.kill()
            await process.wait()
            raise

    async def __call__(self, cmd: List[str]) -> AsyncCompletedProcess:
        """使实例可直接调用"""
        return await self.run(cmd)
