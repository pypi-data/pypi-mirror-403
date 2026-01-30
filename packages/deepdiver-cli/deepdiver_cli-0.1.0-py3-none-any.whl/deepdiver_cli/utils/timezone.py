"""Timezone utilities for consistent datetime handling across the application."""

from datetime import datetime, timezone
from typing import Optional


def now() -> datetime:
    """Get current time in UTC timezone.

    Returns:
        Current datetime with UTC timezone info
    """
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """Get current time in local timezone.

    Returns:
        Current datetime with local timezone info
    """
    return datetime.now().astimezone()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string, converting to local timezone if needed.

    Args:
        dt: Datetime object
        format_str: strftime format string

    Returns:
        Formatted datetime string in local timezone
    """
    # Convert to local timezone if naive or UTC
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()
    return local_dt.strftime(format_str)


def from_isoformat(iso_str: str) -> datetime:
    """Parse ISO format string to datetime with timezone.

    Args:
        iso_str: ISO format datetime string (may or may not have timezone)

    Returns:
        Datetime object with timezone info
    """
    # Remove trailing Z if present (indicates UTC)
    if iso_str.endswith('Z'):
        iso_str = iso_str[:-1]

    dt = datetime.fromisoformat(iso_str)

    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt
