"""Session manager providing high-level session operations."""

from typing import List, Optional
from pathlib import Path
import logging

from deepdiver_cli.utils.timezone import now
from .models import SessionMetadata, SessionStatus
from .repository import SessionRepository
from .factory import SessionFactory
from .exceptions import SessionError, SessionNotFoundError

logger = logging.getLogger(__name__)


class SessionManager:
    """Session manager providing high-level session operations."""

    def __init__(self, repository: SessionRepository):
        """Initialize with a session repository.

        Args:
            repository: Session repository implementation
        """
        self.repository = repository

    def create_session(self, metadata: SessionMetadata) -> SessionMetadata:
        """Create a new session.

        Args:
            metadata: Session metadata to create

        Returns:
            Created session metadata

        Raises:
            SessionError: If creation fails
        """
        logger.info(f"Creating session: {metadata.session_id}")
        return self.repository.create(metadata)

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session information.

        Args:
            session_id: Session ID

        Returns:
            Session metadata if found, None otherwise

        Raises:
            SessionError: If retrieval fails
        """
        return self.repository.get(session_id)

    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        summary_report: Optional[str] = None
    ) -> SessionMetadata:
        """Update session status.

        Args:
            session_id: Session ID
            status: New session status
            summary_report: Path to summary report relative to session directory

        Returns:
            Updated session metadata

        Raises:
            SessionNotFoundError: If session not found
            SessionError: If update fails
        """
        logger.info(f"Updating session {session_id} status to {status}")

        metadata = self.repository.get(session_id)
        if not metadata:
            raise SessionNotFoundError(f"Session {session_id} not found")

        metadata.status = status
        if status in [SessionStatus.FINISHED, SessionStatus.FAILED]:
            metadata.finished_at = now()

        if summary_report:
            metadata.summary_report = summary_report

        return self.repository.update(session_id, metadata)

    def list_sessions(
        self,
        status_filter: Optional[SessionStatus] = None,
        limit: Optional[int] = None
    ) -> List[SessionMetadata]:
        """List sessions with optional filtering and pagination.

        Args:
            status_filter: Filter by session status
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata, sorted by creation time (newest first)

        Raises:
            SessionError: If listing fails
        """
        sessions = self.repository.list_all()

        if status_filter:
            sessions = [s for s in sessions if s.status == status_filter]

        if limit and limit > 0:
            sessions = sessions[:limit]

        logger.debug(f"Listed {len(sessions)} sessions (filter: {status_filter}, limit: {limit})")
        return sessions

    def get_session_report(self, session_id: str) -> Optional[str]:
        """Get session report content.

        Args:
            session_id: Session ID

        Returns:
            Report content if found, None otherwise

        Raises:
            SessionNotFoundError: If session not found
        """
        metadata = self.repository.get(session_id)
        if not metadata:
            raise SessionNotFoundError(f"Session {session_id} not found")

        if not metadata.summary_report:
            return None

        report_path = self.repository.get_session_path(session_id) / metadata.summary_report
        if not report_path.exists():
            return None

        try:
            return report_path.read_text(encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to read report for session {session_id}: {e}")
            return None

    def write_session_file(
        self,
        session_id: str,
        relative_path: str,
        content: str,
        mode: str = "w"
    ) -> Path:
        """Write a file to session directory.

        Args:
            session_id: Session ID
            relative_path: Relative path within session directory
            content: File content
            mode: File mode ('w' for write, 'a' for append)

        Returns:
            Path to the written file

        Raises:
            SessionNotFoundError: If session not found
            SessionError: If write fails
        """
        session_dir = self.repository.get_session_path(session_id)
        file_path = session_dir / relative_path

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)

            logger.debug(f"Wrote file to session {session_id}: {relative_path}")
            return file_path

        except IOError as e:
            raise SessionError(f"Failed to write file to session {session_id}: {e}")

    def read_session_file(
        self,
        session_id: str,
        relative_path: str
    ) -> Optional[str]:
        """Read a file from session directory.

        Args:
            session_id: Session ID
            relative_path: Relative path within session directory

        Returns:
            File content if found, None otherwise

        Raises:
            SessionNotFoundError: If session not found
        """
        session_dir = self.repository.get_session_path(session_id)
        file_path = session_dir / relative_path

        if not file_path.exists():
            return None

        try:
            return file_path.read_text(encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to read file from session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found

        Raises:
            SessionError: If deletion fails
        """
        logger.info(f"Deleting session: {session_id}")
        return self.repository.delete(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session ID

        Returns:
            True if session exists, False otherwise
        """
        return self.repository.exists(session_id)

    def get_session_directory(self, session_id: str) -> Path:
        """Get session directory path.

        Args:
            session_id: Session ID

        Returns:
            Path to session directory

        Raises:
            SessionNotFoundError: If session not found
        """
        return self.repository.get_session_path(session_id)