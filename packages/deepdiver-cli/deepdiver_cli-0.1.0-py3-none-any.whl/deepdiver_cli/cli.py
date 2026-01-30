import sys
from typing import Annotated, List, Optional
from pathlib import Path
import asyncio

import typer

from deepdiver_cli.app.app import run_cli
from deepdiver_cli.config import APIKeyNotConfiguredError
from deepdiver_cli.task import TaskInput, Runtime, WorkDirType
from deepdiver_cli.utils.timezone import format_datetime
from deepdiver_cli.session import (
    FileSystemSessionRepository,
    SessionManager,
    SessionStatus,
)


cli = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@cli.callback(invoke_without_command=True)
def deepdiver(
    ctx: typer.Context,
    is_cwd_code_dir: Annotated[
        bool,
        typer.Option(
            "--code",
            help="Declare that the current working directory is the code directory.",
        ),
    ] = False,
    code_paths: Annotated[
        Optional[List[Path]],
        typer.Option(
            "--code-path",
            exists=True,
            help="Code path associated with the issue: --code-path path1 --code-path path2",
        ),
    ] = None,
    attachment_paths: Annotated[
        Optional[List[Path]],
        typer.Option(
            "--attachment-path",
            exists=True,
            help="Attachment path associated with the issue: --attachment-path path1 --attachment-path path2",
        ),
    ] = None,
    issue: Annotated[
        Optional[str],
        typer.Option(
            ...,
            "--issue",
            "-i",
            help="Issue details",
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="LLM model name of DeepDiver agent"),
    ] = None
):
    # If a subcommand is being invoked, don't run the main CLI flow
    if ctx.invoked_subcommand is not None:
        return

    if not issue:
        typer.echo(
            "Please enter the issue details (type 'EOF' and press Enter to end or use Ctrl+D (Linux/Mac) or Ctrl+Z (Win) to end):"
        )
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
        except EOFError:
            # Use Ctrl+D (Linux/Mac) or Ctrl+Z (Win) to exit.
            pass
        issue = "\n".join(lines)

    try:
        asyncio.run(
            run_cli(
                create_task_input(is_cwd_code_dir, code_paths, attachment_paths, issue),
                create_runtime(model),
            )
        )
    except APIKeyNotConfiguredError as e:
        typer.echo(f"\n⚠️  Configuration Error:\n{e}\n", err=True)
        typer.echo("💡 Tip: You can open the config file with: vi ~/.deepdiver/config/config.toml\n", err=True)
        sys.exit(1)


def create_task_input(
    is_cwd_code_dir: bool,
    code_paths: Optional[List[Path]],
    attachment_paths: Optional[List[Path]],
    issue: str,
) -> TaskInput:
    cwd = Path.cwd()
    code_roots: List[str] = [str(cwd)] if (is_cwd_code_dir and cwd) else []
    attachment_roots: List[str] = [str(cwd)] if (not is_cwd_code_dir and cwd) else []
    if code_paths:
        code_roots.extend([str(path) for path in code_paths])
    if attachment_paths:
        attachment_roots.extend(str(path) for path in attachment_paths)

    return TaskInput(
        description=issue,
        code_roots=code_roots,
        attachment_roots=attachment_roots,
        work_dir=str(cwd),
        work_dir_type=WorkDirType.CODE if is_cwd_code_dir else WorkDirType.ATTACHMENT,
    )


def create_runtime(model: Optional[str]) -> Runtime:
    return Runtime(model=model)


@cli.command(name="list-sessions")
def list_sessions(
    status: Annotated[
        Optional[str],
        typer.Option("--status", help="Filter by status (running/finished/failed)")
    ] = None,
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-n", help="Limit number of sessions shown")
    ] = 10,
):
    """List all sessions."""
    try:
        repository = FileSystemSessionRepository()
        manager = SessionManager(repository)

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = SessionStatus(status.lower())
            except ValueError:
                typer.echo(f"Invalid status: {status}. Must be one of: running, finished, failed", err=True)
                return

        sessions = manager.list_sessions(status_filter=status_filter, limit=limit)

        if not sessions:
            typer.echo("No sessions found.")
            return

        # Simple table output without external dependencies
        headers = ["SESSION_ID", "CREATED_AT", "STATUS", "ISSUE"]
        rows = []
        for session in sessions:
            # Replace newlines and multiple spaces with single space for single-line display
            issue_text = (session.issue_description or "")
            import re
            issue_text = re.sub(r'\s+', ' ', issue_text).strip()

            # Truncate to 50 characters with ellipsis if too long
            issue_preview = issue_text[:50] + "..." if len(issue_text) > 50 else issue_text

            rows.append([
                session.session_id,
                format_datetime(session.created_at),
                session.status.value,
                issue_preview
            ])

        # Calculate column widths
        col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]

        # Print header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        typer.echo(header_row)
        typer.echo("-" * len(header_row))

        # Print rows
        for row in rows:
            typer.echo(" | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)))

        typer.echo(f"\nTotal: {len(sessions)} session(s)")

    except Exception as e:
        typer.echo(f"Error listing sessions: {e}", err=True)


@cli.command(name="show-report")
def show_report(
    session_id: Annotated[
        str,
        typer.Argument(help="Session ID to show report for")
    ],
):
    """Show report for a specific session."""
    try:
        repository = FileSystemSessionRepository()
        manager = SessionManager(repository)

        report_content = manager.get_session_report(session_id)
        if not report_content:
            typer.echo(f"No report found for session {session_id}", err=True)
            return

        typer.echo(report_content)

    except Exception as e:
        typer.echo(f"Error showing report: {e}", err=True)


def main():
    sys.exit(cli())


if __name__ == "__main__":
    main()
