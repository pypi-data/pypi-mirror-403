"""Data models for session management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

from deepdiver_cli.utils.timezone import now


class SessionStatus(str, Enum):
    """Session status enumeration."""
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class CwdRole(str, Enum):
    """Current working directory role enumeration."""
    CODE = "code"
    ATTACHMENTS = "attachments"


class SessionMetadata(BaseModel):
    """Session metadata corresponding to meta.json file structure.

    Follows the specification in CLI.md.
    """

    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(default_factory=now, description="Creation time (UTC)")
    finished_at: Optional[datetime] = Field(None, description="Completion time (UTC)")
    status: SessionStatus = Field(default=SessionStatus.RUNNING, description="Session status")

    issue_description: Optional[str] = Field(None, description="Issue description")

    code_roots: List[str] = Field(default_factory=list, description="Code root directories")
    attachment_roots: List[str] = Field(default_factory=list, description="Attachment root directories")
    cwd_role: Optional[CwdRole] = Field(None, description="Current working directory role")

    cli_args: List[str] = Field(default_factory=list, description="CLI arguments")
    agent_version: str = Field(default="0.1.0", description="Agent version")

    summary_report: Optional[str] = Field(None, description="Path to summary report relative to session directory")

    # Extension fields for custom metadata
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        },
        populate_by_name=True,
        extra="ignore"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        """Create from dictionary with proper datetime parsing."""
        from deepdiver_cli.utils.timezone import from_isoformat

        # Parse datetime fields
        for date_field in ["created_at", "finished_at"]:
            if date_field in data and data[date_field]:
                if isinstance(data[date_field], str):
                    data[date_field] = from_isoformat(data[date_field])

        return cls.model_validate(data)


# Constants for directory structure (moved from old session.py)
ARTIFACTS_DIR = "artifacts"
REPORTS_DIR = "reports"
LOGS_DIR = "logs"
INPUT_DIR = "input"
CHAT_DIR = "chat"
META_FILE = "meta.json"

# Subdirectories within artifacts
LOGS_PARSED_DIR = "logs_parsed"

# Report files
SUMMARY_MD = "summary.md"
SUMMARY_JSON = "summary.json"
TIMELINE_MD = "timeline.md"

# Input files
ENV_SNAPSHOT_JSON = "env_snapshot.json"
FILE_MANIFEST_JSON = "file_manifest.json"
RAW_PROMPT_TXT = "raw_prompt.txt"