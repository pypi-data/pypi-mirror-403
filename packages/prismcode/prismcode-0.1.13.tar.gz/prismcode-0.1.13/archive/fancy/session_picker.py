"""Session picker for startup."""
from rich.console import Console
from rich.table import Table

from core.history import list_sessions


def show_session_picker() -> str | None:
    """Show session picker on startup. Returns session_id or None for new session."""
    console = Console()
    sessions = list_sessions(limit=10)

    if not sessions:
        return None  # No previous sessions, start fresh

    console.print("\n[bold cyan]📚 Prism Sessions[/]\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Session ID", style="cyan")
    table.add_column("Messages", justify="right")
    table.add_column("Preview", style="dim")

    for i, session in enumerate(sessions, 1):
        preview = session.get("preview", "")[:40]
        if len(session.get("preview", "")) > 40:
            preview += "..."
        table.add_row(
            str(i),
            session["id"],
            str(session.get("message_count", 0)),
            preview
        )

    console.print(table)
    console.print("\n[dim]Enter number to continue session, or press Enter for new session:[/]")

    try:
        choice = input("> ").strip()
        if not choice:
            return None  # New session
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx]["id"]
        # Try as session ID directly
        for session in sessions:
            if session["id"].startswith(choice):
                return session["id"]
    except (KeyboardInterrupt, EOFError):
        pass

    return None
