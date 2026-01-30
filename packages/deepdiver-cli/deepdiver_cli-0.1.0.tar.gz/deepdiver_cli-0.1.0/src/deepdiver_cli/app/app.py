from enum import Enum
import json
from pathlib import Path
import sys
import time


from deepdiver_cli.logger import logger, setup_session_logging
from deepdiver_cli.plugin import create_plugin
from deepdiver_cli.plugins.datafilter import NoOpFilter
from deepdiver_cli.plugins.datamask import NoOpMasker
from deepdiver_cli.plugins.descyptor import NoOpDecryptor
from deepdiver_cli.task import TaskInput, Runtime
from deepdiver_cli.tools import (
    GrepTool,
    GlobTool,
    ReadTool,
    ProcessFileTool,
    LoadKnowledgeTool,
    AskHumanTool,
    FinishTool,
    InspectTool,
    ReviewTool,
    AnalyzeCodeTool,
    WriteReportTool,
)

from deepdiver_cli.react_core.llm import LLMClient
from deepdiver_cli.react_core.tool import ToolRegistry
from deepdiver_cli.react_core.agent import ReActAgent, ReActAgentConfig
from deepdiver_cli.utils.measure_time import auto_time_unit
from deepdiver_cli.config import config
from deepdiver_cli.app.processor import (
    set_desensitizer,
    set_decryptor,
    get_desensitizer,
    set_filter,
)

# Session management imports
from deepdiver_cli.session import (
    FileSystemSessionRepository,
    SessionFactory,
    SessionManager,
    SessionStatus,
    Session,
)


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


async def run_cli(task: TaskInput, runtime: Runtime):
    # Initialize session management
    repository = FileSystemSessionRepository()
    session_manager = SessionManager(repository)

    # Create session metadata from task input
    metadata = SessionFactory.create_from_task_input(
        task_input=task, cli_args=sys.argv, agent_version="0.1.0"
    )

    # Create session
    metadata = session_manager.create_session(metadata)
    session = Session(metadata, repository)

    # Setup logging for this session
    setup_session_logging(session.session_dir)

    logger.info(f"Created session: {session.session_id}")

    # Write raw prompt to input directory
    raw_prompt = _build_issue(task)
    session.write_raw_prompt(raw_prompt)

    # Write environment snapshot (basic info)
    env_snapshot = json.dumps(
        {
            "python_version": sys.version,
            "working_directory": str(Path.cwd()),
            "task": task.model_dump(exclude_none=True),
        },
        indent=2,
        cls=EnumEncoder,
    )
    session.write_env_snapshot(env_snapshot)

    # Write file manifest
    file_manifest = json.dumps(
        {
            "code_roots": task.code_roots,
            "attachment_roots": task.attachment_roots,
            "work_dir": task.work_dir,
        },
        indent=2,
    )
    session.write_file_manifest(file_manifest)

    # Setup plugins
    setup_plugins()

    # Get tools with session context
    tools = _get_tools(task, session)
    tool_registry = ToolRegistry()
    for tool in tools:
        tool_registry.register(tool)

    # Create agent
    agent = ReActAgent(
        llm=LLMClient(config.deepdiver.llm[runtime.model or "default"]),
        tools=tool_registry,
        config=ReActAgentConfig(
            max_steps=config.deepdiver.max_steps,
            finish_tool_name=FinishTool().name,
        ),
    )

    # Run analysis
    start_time = time.perf_counter()
    try:
        logger.info("issue", issue=raw_prompt)
        await agent.aask(get_desensitizer().mask(raw_prompt))
        logger.warn(
            "task.finish", cost=auto_time_unit(time.perf_counter() - start_time)
        )

        # Update session status to finished
        session.update_status(
            SessionStatus.FINISHED, summary_report="reports/summary.md"
        )
        logger.info(f"Session {session.session_id} finished successfully")

    except Exception as e:
        # Update session status to failed
        logger.error(f"Session {session.session_id} failed: {e}")
        session.update_status(SessionStatus.FAILED)
        raise


def setup_plugins():
    plugin_dir = str(Path(config.plugin.plugin_dir).expanduser().absolute())
    sys.path.insert(0, plugin_dir)
    # Build mapping from plugin key to path
    plugin_map = {}
    for item in config.plugin.plugins:
        if item.key not in plugin_map:  # first wins
            plugin_map[item.key] = item.path

    desensitizer = create_plugin(plugin_map.get("desensitizer"))
    if desensitizer:
        set_desensitizer(desensitizer)
    decryptor = create_plugin(plugin_map.get("decryptor"))
    if decryptor:
        set_decryptor(decryptor)
    filter = create_plugin(plugin_map.get("filter"))
    if filter:
        set_filter(filter)

    logger.info(
        "setup_plugins",
        desensitizer="On" if type(desensitizer) is not NoOpMasker else "Off",
        decryptor="On" if type(decryptor) is not NoOpDecryptor else "Off",
        filter="On" if type(filter) is not NoOpFilter else "Off",
    )


def _get_tools(
    task: TaskInput,
    session: Session,
):
    allow_dirs = {
        task.work_dir,
        *task.code_roots,
        *task.attachment_roots,
        str(session.logs_parsed_dir),  # Include session's logs_parsed directory
    }
    tools = [
        GrepTool(allow_dirs),
        GlobTool(allow_dirs),
        ReadTool(allow_dirs),
        ProcessFileTool(allow_dirs, session),
        LoadKnowledgeTool(),
        AskHumanTool(),
        FinishTool(),
        WriteReportTool(session),
    ]

    # Conditionally add InspectTool based on config
    if config.tools.inspect.enable:
        tools.append(InspectTool(allow_dirs))

    # Conditionally add ReviewTool based on config
    if config.tools.review.enable:
        tools.append(ReviewTool())

    # Conditionally add AnalyzeCodeTool based on config
    if config.tools.analyze_code.enable and task.code_roots:
        tools.append(AnalyzeCodeTool(allow_dirs))

    return tools


def _build_issue(task: TaskInput) -> str:
    return json.dumps(
        task.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=4,
        cls=EnumEncoder,
    )
