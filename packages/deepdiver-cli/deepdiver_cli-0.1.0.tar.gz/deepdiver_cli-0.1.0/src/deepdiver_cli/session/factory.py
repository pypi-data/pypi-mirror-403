"""Session factory for creating new sessions."""

import random
import string
from datetime import datetime
from typing import List, Optional
import logging

from deepdiver_cli.task import TaskInput, WorkDirType
from deepdiver_cli.utils.timezone import now_local
from .models import SessionMetadata, SessionStatus, CwdRole

logger = logging.getLogger(__name__)


class SessionFactory:
    """Factory for creating new sessions and generating session IDs."""

    @staticmethod
    def generate_session_id() -> str:
        """Generate a session ID in format: YYYYMMDD_HHMMSS_random6.

        Uses local timezone for the timestamp.

        Returns:
            Generated session ID
        """
        timestamp = now_local().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        session_id = f"{timestamp}_{random_suffix}"
        logger.debug(f"Generated session ID: {session_id}")
        return session_id

    @classmethod
    def create_from_task_input(
        cls,
        task_input: TaskInput,
        cli_args: List[str],
        agent_version: str = "0.1.0"
    ) -> SessionMetadata:
        """Create session metadata from task input.

        Args:
            task_input: Task input containing issue description and directories
            cli_args: Original CLI arguments
            agent_version: Agent version string

        Returns:
            Session metadata
        """
        session_id = cls.generate_session_id()

        # Convert work directory type
        cwd_role = (
            CwdRole.CODE
            if task_input.work_dir_type == WorkDirType.CODE
            else CwdRole.ATTACHMENTS
        )

        metadata = SessionMetadata(
            session_id=session_id,
            status=SessionStatus.RUNNING,
            issue_description=task_input.description,
            code_roots=task_input.code_roots,
            attachment_roots=task_input.attachment_roots,
            cwd_role=cwd_role,
            cli_args=cli_args,
            agent_version=agent_version,
        )

        logger.info(f"Created session metadata from task input: {session_id}")
        return metadata

    @classmethod
    def create_from_cli_args(
        cls,
        issue_description: Optional[str],
        code_roots: List[str],
        attachment_roots: List[str],
        cwd_role: CwdRole,
        cli_args: List[str],
        agent_version: str = "0.1.0"
    ) -> SessionMetadata:
        """Create session metadata from CLI arguments.

        Args:
            issue_description: Issue description (optional)
            code_roots: List of code root directories
            attachment_roots: List of attachment root directories
            cwd_role: Current working directory role
            cli_args: CLI arguments
            agent_version: Agent version string

        Returns:
            Session metadata
        """
        session_id = cls.generate_session_id()

        metadata = SessionMetadata(
            session_id=session_id,
            status=SessionStatus.RUNNING,
            issue_description=issue_description,
            code_roots=code_roots,
            attachment_roots=attachment_roots,
            cwd_role=cwd_role,
            cli_args=cli_args,
            agent_version=agent_version,
        )

        logger.info(f"Created session metadata from CLI args: {session_id}")
        return metadata

    @classmethod
    def create_empty_session(cls, agent_version: str = "0.1.0") -> SessionMetadata:
        """Create an empty session metadata (for testing or manual creation).

        Args:
            agent_version: Agent version string

        Returns:
            Session metadata
        """
        session_id = cls.generate_session_id()

        metadata = SessionMetadata(
            session_id=session_id,
            status=SessionStatus.RUNNING,
            agent_version=agent_version,
        )

        logger.info(f"Created empty session metadata: {session_id}")
        return metadata