"""File system implementation of session repository."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from deepdiver_cli.config import SESSION_ROOT
from .models import SessionMetadata, SessionStatus
from .repository import SessionRepository
from .exceptions import SessionError, SessionNotFoundError, SessionValidationError, SessionStorageError

logger = logging.getLogger(__name__)


class FileSystemSessionRepository(SessionRepository):
    """File system based session storage implementation."""

    def __init__(self, sessions_root: Path = SESSION_ROOT):
        """Initialize with sessions root directory.

        Args:
            sessions_root: Root directory for sessions (default: SESSION_ROOT from config)
        """
        self.sessions_root = sessions_root
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    def _get_session_dir(self, session_id: str) -> Path:
        """Get session directory path.

        Args:
            session_id: Session ID

        Returns:
            Path to session directory
        """
        return self.sessions_root / session_id

    def _get_meta_file(self, session_id: str) -> Path:
        """Get meta.json file path.

        Args:
            session_id: Session ID

        Returns:
            Path to meta.json file
        """
        return self._get_session_dir(session_id) / "meta.json"

    def _create_session_directory_structure(self, session_dir: Path) -> None:
        """Create session directory structure.

        Args:
            session_dir: Session directory path

        Raises:
            SessionStorageError: If directory creation fails
        """
        try:
            # Create main directory
            session_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            subdirs = [
                "input",
                "artifacts",
                "reports",
                "patches",
                "logs",
                "artifacts/logs_parsed",
            ]
            for subdir in subdirs:
                (session_dir / subdir).mkdir(parents=True, exist_ok=True)

            logger.debug(f"Created session directory structure at {session_dir}")

        except OSError as e:
            raise SessionStorageError(f"Failed to create session directory structure: {e}")

    def create(self, metadata: SessionMetadata) -> SessionMetadata:
        """Create a new session directory and metadata file.

        Args:
            metadata: Session metadata to create

        Returns:
            Created session metadata

        Raises:
            SessionError: If creation fails
        """
        session_dir = self._get_session_dir(metadata.session_id)

        if session_dir.exists():
            raise SessionError(f"Session {metadata.session_id} already exists")

        try:
            # Create directory structure
            self._create_session_directory_structure(session_dir)

            # Write metadata
            meta_file = self._get_meta_file(metadata.session_id)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            logger.info(f"Created session {metadata.session_id} at {session_dir}")
            return metadata

        except (OSError, TypeError) as e:
            # Clean up on error
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
            raise SessionStorageError(f"Failed to create session {metadata.session_id}: {e}")

    def get(self, session_id: str) -> Optional[SessionMetadata]:
        """Read session metadata.

        Args:
            session_id: Session ID

        Returns:
            Session metadata if found, None otherwise

        Raises:
            SessionError: If retrieval fails
        """
        meta_file = self._get_meta_file(session_id)
        if not meta_file.exists():
            return None

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return SessionMetadata.from_dict(data)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise SessionError(f"Failed to read session metadata for {session_id}: {e}")

    def update(self, session_id: str, metadata: SessionMetadata) -> SessionMetadata:
        """Update session metadata.

        Args:
            session_id: Session ID
            metadata: Updated session metadata

        Returns:
            Updated session metadata

        Raises:
            SessionNotFoundError: If session not found
            SessionError: If update fails
        """
        if session_id != metadata.session_id:
            raise SessionValidationError("Session ID mismatch")

        meta_file = self._get_meta_file(session_id)
        if not meta_file.exists():
            raise SessionNotFoundError(f"Session {session_id} does not exist")

        try:
            # Write updated metadata
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            logger.debug(f"Updated session metadata for {session_id}")
            return metadata

        except (OSError, TypeError) as e:
            raise SessionStorageError(f"Failed to update session {session_id}: {e}")

    def list_all(self) -> List[SessionMetadata]:
        """List all sessions.

        Returns:
            List of session metadata, sorted by creation time (newest first)

        Raises:
            SessionError: If listing fails
        """
        sessions = []
        try:
            for session_dir in self.sessions_root.iterdir():
                if session_dir.is_dir():
                    try:
                        metadata = self.get(session_dir.name)
                        if metadata:
                            sessions.append(metadata)
                    except SessionError as e:
                        # Skip corrupted session directories but log warning
                        logger.warning(f"Skipping corrupted session directory {session_dir.name}: {e}")
                        continue

            # Sort by creation time, newest first
            return sorted(sessions, key=lambda x: x.created_at, reverse=True)

        except OSError as e:
            raise SessionStorageError(f"Failed to list sessions: {e}")

    def delete(self, session_id: str) -> bool:
        """Delete session directory.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found

        Raises:
            SessionError: If deletion fails
        """
        session_dir = self._get_session_dir(session_id)
        if not session_dir.exists():
            return False

        try:
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session {session_id}")
            return True

        except OSError as e:
            raise SessionStorageError(f"Failed to delete session {session_id}: {e}")

    def get_session_path(self, session_id: str) -> Path:
        """Get session directory path.

        Args:
            session_id: Session ID

        Returns:
            Path to session directory

        Raises:
            SessionNotFoundError: If session not found
        """
        session_dir = self._get_session_dir(session_id)
        if not session_dir.exists():
            raise SessionNotFoundError(f"Session {session_id} does not exist")
        return session_dir

    def exists(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id: Session ID

        Returns:
            True if session exists, False otherwise
        """
        return self._get_meta_file(session_id).exists()