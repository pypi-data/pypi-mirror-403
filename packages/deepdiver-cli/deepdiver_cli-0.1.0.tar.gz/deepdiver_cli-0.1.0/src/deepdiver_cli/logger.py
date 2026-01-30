import json
import os
import logging
import structlog
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from deepdiver_cli.config import SESSION_ROOT


_global_logger = None


def configure_logging(session_log_dir: Optional[Path] = None):
    """配置日志系统。

    Args:
        session_log_dir: 会话特定的日志目录。如果提供，日志将写入到该目录；
                     否则使用全局日志目录。

    Returns:
        配置好的logger实例
    """
    log_level = os.getenv("DEEP_DIVER_LOG_LEVEL", "WARNING").upper()

    # 1. 创建控制台处理器（带颜色）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))

    # 2. 确定日志目录
    if session_log_dir:
        log_dir = session_log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        # 使用全局日志目录（用于CLI命令等非会话操作）
        log_dir = SESSION_ROOT / "_global_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

    # 3. 创建文件处理器（JSON格式）
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # 文件记录更详细

    # 4. 配置标准 logging
    root_logger = logging.getLogger()
    # 清除已有的handlers，避免重复添加
    root_logger.handlers.clear()

    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 5. 配置 structlog 处理器链
    structlog.configure(
        processors=[
            # 通用处理器
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # 根据处理器类型分流
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 6. 为不同处理器设置不同渲染器
    console_processor = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(colors=True),  # 彩色控制台
    ]

    file_processor = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.processors.JSONRenderer(
            serializer=lambda obj, **kwargs: json.dumps(obj, ensure_ascii=False)
        ),
    ]

    # 应用格式化器
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(processors=console_processor)
    )
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(processors=file_processor)
    )

    return structlog.get_logger()


# 初始化全局logger（使用全局日志目录）
logger = configure_logging()


def setup_session_logging(session_dir: Path) -> Path:
    """为会话设置日志系统。

    Args:
        session_dir: 会话目录路径

    Returns:
        日志文件目录路径
    """
    log_dir = session_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 重新配置日志系统，使用会话特定的日志目录
    configure_logging(session_log_dir=log_dir)

    return log_dir

