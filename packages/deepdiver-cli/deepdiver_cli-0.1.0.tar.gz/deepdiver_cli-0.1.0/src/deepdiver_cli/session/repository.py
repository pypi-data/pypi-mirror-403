"""Session repository abstraction interface."""

from typing import Protocol, List, Optional
from pathlib import Path

from .models import SessionMetadata


class SessionRepository(Protocol):
    """Abstract interface for session storage.

    Follows the dependency inversion principle - high-level modules depend on this abstraction,
    not on concrete implementations.
    """

    def create(self, metadata: SessionMetadata) -> SessionMetadata:
        """Create a new session.

        Args:
            metadata: Session metadata to create

        Returns:
            Created session metadata

        Raises:
            SessionError: If creation fails
        """
        raise NotImplementedError

    def get(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata.

        Args:
            session_id: Session ID

        Returns:
            Session metadata if found, None otherwise

        Raises:
            SessionError: If retrieval fails
        """
        raise NotImplementedError

    def update(self, session_id: str, metadata: SessionMetadata) -> SessionMetadata:
        """Update session metadata.

        Args:
            session_id: Session ID
            metadata: Updated session metadata

        Returns:
            Updated session metadata

        Raises:
            SessionError: If update fails
            SessionNotFoundError: If session not found
        """
        raise NotImplementedError

    def list_all(self) -> List[SessionMetadata]:
        """List all sessions.

        Returns:
            List of session metadata, sorted by creation time (newest first)

        Raises:
            SessionError: If listing fails
        """
        raise NotImplementedError

    def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found

        Raises:
            SessionError: If deletion fails
        """
        raise NotImplementedError

    def get_session_path(self, session_id: str) -> Path:
        """Get session directory path.

        Args:
            session_id: Session ID

        Returns:
            Path to session directory

        Raises:
            SessionNotFoundError: If session not found
        """
        raise NotImplementedError

    def exists(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id: Session ID

        Returns:
            True if session exists, False otherwise
        """
        raise NotImplementedError