"""Session class encapsulating operations for a single session."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from deepdiver_cli.utils.timezone import now
from .models import (
    SessionMetadata, SessionStatus,
    ARTIFACTS_DIR, REPORTS_DIR, LOGS_DIR, INPUT_DIR,
    LOGS_PARSED_DIR,
    SUMMARY_MD, SUMMARY_JSON, TIMELINE_MD,
    ENV_SNAPSHOT_JSON, FILE_MANIFEST_JSON, RAW_PROMPT_TXT
)
from .repository import SessionRepository
from .exceptions import SessionError, SessionNotFoundError

logger = logging.getLogger(__name__)


class Session:
    """Session class encapsulating operations for a single session."""

    def __init__(self, metadata: SessionMetadata, repository: SessionRepository):
        """Initialize with session metadata and repository.

        Args:
            metadata: Session metadata
            repository: Session repository
        """
        self.metadata = metadata
        self.repository = repository
        self._session_dir = repository.get_session_path(metadata.session_id)

    @property
    def session_id(self) -> str:
        """Get session ID."""
        return self.metadata.session_id

    @property
    def session_dir(self) -> Path:
        """Get session directory path."""
        return self._session_dir

    @property
    def input_dir(self) -> Path:
        """Get input directory path."""
        return self._session_dir / INPUT_DIR

    @property
    def artifacts_dir(self) -> Path:
        """Get artifacts directory path."""
        return self._session_dir / ARTIFACTS_DIR

    @property
    def reports_dir(self) -> Path:
        """Get reports directory path."""
        return self._session_dir / REPORTS_DIR

    @property
    def patches_dir(self) -> Path:
        """Get patches directory path."""
        return self._session_dir / "patches"

    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        return self._session_dir / LOGS_DIR

    @property
    def logs_parsed_dir(self) -> Path:
        """Get logs parsed directory path."""
        return self.artifacts_dir / LOGS_PARSED_DIR

    def update_status(
        self,
        status: SessionStatus,
        summary_report: Optional[str] = None
    ) -> None:
        """Update session status.

        Args:
            status: New session status
            summary_report: Path to summary report relative to session directory
        """
        self.metadata.status = status
        if status in [SessionStatus.FINISHED, SessionStatus.FAILED]:
            self.metadata.finished_at = now()

        if summary_report:
            self.metadata.summary_report = summary_report

        self.repository.update(self.session_id, self.metadata)
        logger.info(f"Updated session {self.session_id} status to {status}")

    def write_input_file(self, filename: str, content: str, mode: str = "w") -> Path:
        """Write a file to input directory.

        Args:
            filename: Filename (without path)
            content: File content
            mode: File mode ('w' for write, 'a' for append)

        Returns:
            Path to the written file
        """
        file_path = self.input_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Wrote input file: {filename}")
        return file_path

    def write_raw_prompt(self, content: str) -> Path:
        """Write raw prompt to input directory.

        Args:
            content: Raw prompt content

        Returns:
            Path to the written file
        """
        return self.write_input_file(RAW_PROMPT_TXT, content)

    def write_env_snapshot(self, content: str) -> Path:
        """Write environment snapshot to input directory.

        Args:
            content: Environment snapshot JSON content

        Returns:
            Path to the written file
        """
        return self.write_input_file(ENV_SNAPSHOT_JSON, content)

    def write_file_manifest(self, content: str) -> Path:
        """Write file manifest to input directory.

        Args:
            content: File manifest JSON content

        Returns:
            Path to the written file
        """
        return self.write_input_file(FILE_MANIFEST_JSON, content)

    def write_report(self, filename: str, content: str) -> Path:
        """Write a file to reports directory.

        Args:
            filename: Filename (without path)
            content: File content

        Returns:
            Path to the written file
        """
        file_path = self.reports_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Wrote report file: {filename}")
        return file_path

    def write_summary_md(self, content: str) -> Path:
        """Write summary markdown to reports directory.

        Args:
            content: Summary markdown content

        Returns:
            Path to the written file
        """
        return self.write_report(SUMMARY_MD, content)

    def write_summary_json(self, content: str) -> Path:
        """Write summary JSON to reports directory.

        Args:
            content: Summary JSON content

        Returns:
            Path to the written file
        """
        return self.write_report(SUMMARY_JSON, content)

    def write_timeline_md(self, content: str) -> Path:
        """Write timeline markdown to reports directory.

        Args:
            content: Timeline markdown content

        Returns:
            Path to the written file
        """
        return self.write_report(TIMELINE_MD, content)

    def write_artifact(self, relative_path: str, content: str) -> Path:
        """Write a file to artifacts directory.

        Args:
            relative_path: Relative path within artifacts directory
            content: File content

        Returns:
            Path to the written file
        """
        file_path = self.artifacts_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Wrote artifact: {relative_path}")
        return file_path

    def write_patch(self, filename: str, content: str) -> Path:
        """Write a patch file to patches directory.

        Args:
            filename: Filename (without path)
            content: Patch content

        Returns:
            Path to the written file
        """
        file_path = self.patches_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Wrote patch file: {filename}")
        return file_path

    def write_log(self, filename: str, content: str) -> Path:
        """Write a log file to logs directory.

        Args:
            filename: Filename (without path)
            content: Log content

        Returns:
            Path to the written file
        """
        file_path = self.logs_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Wrote log file: {filename}")
        return file_path

    def get_report_content(self, filename: str = SUMMARY_MD) -> Optional[str]:
        """Get report content.

        Args:
            filename: Report filename

        Returns:
            Report content if found, None otherwise
        """
        report_path = self.reports_dir / filename
        if not report_path.exists():
            return None

        try:
            return report_path.read_text(encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to read report {filename}: {e}")
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CLI output.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self.metadata.session_id,
            "created_at": self.metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.metadata.status.value,
            "issue": self.metadata.issue_description or "",
            "code_roots": len(self.metadata.code_roots),
            "attachment_roots": len(self.metadata.attachment_roots),
        }