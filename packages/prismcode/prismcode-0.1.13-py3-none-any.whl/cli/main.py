"""
Terminal interface for Prism agent.
Rich-based UI with proper status indicators and paste handling.
"""
import sys
import time
import threading
from itertools import cycle

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.spinner import Spinner
from rich.console import Group
from rich.rule import Rule

from core.agent import Agent
from core.history import list_sessions
from tools import read_file, create_file, edit_file, rename_file, delete_file, ls
from config import LANG_MAP, AGENT_CONFIG, SLASH_COMMANDS
from themes import THEMES
from settings import Settings

console = Console()


# ============================================================================
# Status Indicator
# ============================================================================

class StatusIndicator:
    """Animated status indicator for inference and tool execution."""
    
    SPINNERS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self):
        self.active = False
        self.status = ""
        self.tokens = 0
        self.tool_name = None
        self._spinner_cycle = cycle(self.SPINNERS)
        self._last_update = 0
    
    def start(self, status: str = "Thinking"):
        """Start the indicator with a status message."""
        self.active = True
        self.status = status
        self.tokens = 0
        self.tool_name = None
    
    def set_streaming(self, tokens: int = 0):
        """Update to streaming mode with token count."""
        self.status = "Streaming"
        self.tokens = tokens
    
    def set_tool(self, tool_name: str):
        """Update to show tool execution."""
        self.status = "Tool"
        self.tool_name = tool_name
    
    def stop(self):
        """Stop the indicator."""
        self.active = False
        self.status = ""
        self.tokens = 0
        self.tool_name = None
    
    def render(self) -> Text:
        """Render the current status as a Rich Text object."""
        if not self.active:
            return Text("")
        
        spinner = next(self._spinner_cycle)
        
        if self.tool_name:
            return Text.assemble(
                (f"{spinner} ", "cyan"),
                ("executing ", "dim"),
                (self.tool_name, "bold cyan"),
                ("...", "dim"),
            )
        elif self.tokens > 0:
            return Text.assemble(
                (f"{spinner} ", "green"),
                ("streaming ", "dim"),
                (f"{self.tokens}", "bold green"),
                (" tokens", "dim"),
            )
        else:
            return Text.assemble(
                (f"{spinner} ", "yellow"),
                (self.status.lower(), "dim"),
                ("...", "dim"),
            )


def render_inline_diff(old_str: str, new_str: str, file_path: str):
    """Render an inline unified diff with syntax highlighting and red/green backgrounds."""
    import difflib

    old_lines = old_str.splitlines()
    new_lines = new_str.splitlines()

    # Get language for syntax highlighting
    ext = file_path.split(".")[-1] if "." in file_path else "text"
    lang = LANG_MAP.get(ext, ext)

    # Compute LCS-based diff
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    diff_lines = []
    stats = {"added": 0, "removed": 0}

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # Context lines - only show up to 2 lines of context
            context_lines = old_lines[i1:i2]
            if len(context_lines) > 4:
                # Show first 2 and last 2 with separator
                for line in context_lines[:2]:
                    diff_lines.append(("context", line))
                diff_lines.append(("separator", None))
                for line in context_lines[-2:]:
                    diff_lines.append(("context", line))
            else:
                for line in context_lines:
                    diff_lines.append(("context", line))
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                diff_lines.append(("removed", line))
                stats["removed"] += 1
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                diff_lines.append(("added", line))
                stats["added"] += 1
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                diff_lines.append(("removed", line))
                stats["removed"] += 1
            for line in new_lines[j1:j2]:
                diff_lines.append(("added", line))
                stats["added"] += 1

    # Print header
    console.print(f"[cyan]│[/]  [dim]📝 {file_path}[/] [green]+{stats['added']}[/] [red]-{stats['removed']}[/]")
    console.print(f"[cyan]│[/]")

    # Print diff lines
    for line_type, content in diff_lines:
        if line_type == "separator":
            console.print(f"[cyan]│[/]  [dim]  ⋯[/]")
        elif line_type == "context":
            # Dim context lines
            console.print(f"[cyan]│[/]  [dim]  {content}[/]")
        elif line_type == "removed":
            # Red background for removed lines
            console.print(f"[cyan]│[/]  [bold red on #3d1a1a]- {content}[/]")
        elif line_type == "added":
            # Green background for added lines
            console.print(f"[cyan]│[/]  [bold green on #1a3d1a]+ {content}[/]")


def render_tool_call(name: str, args: dict, result: str):
    """Render a tool call with nice formatting."""
    settings = Settings()
    console.print(f"[cyan]├─[/] [bold cyan]{name}[/]")

    # Special diff display for edit_file
    if name == "edit_file" and "old_str" in args and "new_str" in args:
        file_path = args.get("file_path", "")

        if settings.show_diff:
            # Show inline unified diff with red/green highlighting
            render_inline_diff(args["old_str"], args["new_str"], file_path)
        else:
            # Show simple one-line summary
            console.print(f"[cyan]│[/]  [dim]└─[/] file_path: [yellow]{file_path}[/]")
            old_lines = len(args["old_str"].splitlines())
            new_lines = len(args["new_str"].splitlines())
            if old_lines == new_lines:
                console.print(f"[cyan]│[/]  [dim]└─[/] modified {old_lines} line{'s' if old_lines != 1 else ''}")
            else:
                console.print(f"[cyan]│[/]  [dim]└─[/] changed {old_lines} → {new_lines} lines")
    else:
        for k, v in args.items():
            display_v = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
            console.print(f"[cyan]│[/]  [dim]└─[/] {k}: [yellow]{display_v}[/]")

    # Result display
    if name == "read_file":
        line_count = len(result.split("\n"))
        console.print(f"[cyan]└─[/] [green]✓[/] Read {line_count} lines")
    else:
        display_result = result[:100] + "..." if len(result) > 100 else result
        console.print(f"[cyan]└─[/] [green]✓[/] {display_result}")
    console.print()


def run_agent_loop(agent: Agent, user_input: str):
    """Run agent and render events to terminal."""
    full_text = ""
    
    console.print("[bold orange1]Prism:[/] ", end="")
    
    for event in agent.stream(user_input):
        if event.type == "text_delta":
            # Print text incrementally (no Live context - preserves scrollback)
            print(event.content, end="", flush=True)
            full_text += event.content
            
        elif event.type == "text_done":
            # Print newline after streaming completes
            print()
            
        elif event.type == "tool_done":
            render_tool_call(event.name, event.arguments, event.result)
    
    console.print()  # Add spacing after response


def load_and_display_chat_history(agent: Agent):
    """Load and display chat history for the current session."""
    if not agent.history.messages:
        return
    
    console.print()
    console.print("[dim]─── Loading chat history ───[/]")
    
    for msg in agent.history.messages:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role == "user":
            console.print()
            console.print(f"[bold yellow]You:[/] {content}")
        elif role == "assistant":
            console.print()
            console.print("[bold orange1]Prism:[/] ", end="")
            try:
                markdown_content = Markdown(content, code_theme="monokai")
                console.print(markdown_content)
            except:
                console.print(content)
        elif role == "tool":
            tool_name = msg.get("tool_name", "tool")
            console.print(f"[cyan]├─[/] [bold cyan]{tool_name}[/]")
    
    console.print()
    console.print("[dim]─── End of history ───[/]")
    console.print()


def handle_slash_command(agent: Agent, command: str) -> bool:
    """Handle slash commands. Returns True if command was handled."""
    parts = command[1:].split()  # Remove leading slash
    if not parts:
        return False
    
    cmd = parts[0].lower()
    
    if cmd == "theme":
        if len(parts) == 1:
            # List available themes
            from themes import THEMES
            themes_list = ", ".join(THEMES.keys())
            console.print()
            console.print(f"[dim]Available themes: {themes_list}[/]")
            console.print(f"[cyan]Current theme: github-dark (default)[/]")
            console.print()
            return True
        
        elif len(parts) == 2:
            console.print()
            console.print("[dim]Theme switching not supported in terminal version[/]")
            console.print("[dim]Use run_fancy.py for theme support[/]")
            console.print()
            return True

    elif cmd == "themes":
        # Show detailed theme info
        from themes import THEMES
        console.print()
        console.print("[bold cyan]🎨 Available Themes:[/]\n")
        for name, theme in THEMES.items():
            console.print(f"  [bold cyan]{name}[/] - {theme['name']}")
        console.print(f"\n[dim]Use run_fancy.py for theme support[/]")
        console.print()
        return True

    elif cmd == "toggle-diff" or cmd == "diff":
        settings = Settings()
        settings.show_diff = not settings.show_diff
        settings.save()
        status = "enabled" if settings.show_diff else "disabled"
        console.print()
        console.print(f"[green]Detailed diff display {status}[/]")
        if not settings.show_diff:
            console.print("[dim]File edits will show simplified one-line summaries[/]")
        else:
            console.print("[dim]File edits will show full before/after diffs[/]")
        console.print()
        return True

    elif cmd == "sessions":
        sessions = list_sessions()
        console.print()
        console.print("[bold cyan]📚 Recent Sessions:[/]\n")
        
        if not sessions:
            console.print("[dim]No sessions found.[/]\n")
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Session ID", style="cyan")
            table.add_column("Messages", justify="right", style="yellow")
            table.add_column("Preview", style="dim")

            for i, session in enumerate(sessions[:10], 1):  # Show last 10 sessions
                session_id = session["id"]
                preview = session.get("preview", "")[:50]
                if len(session.get("preview", "")) > 50:
                    preview += "..."
                msg_count = session.get("message_count", 0)
                
                # Mark current session
                if session_id == agent.history.session_id:
                    table.add_row(f"►{i}", f"{session_id} [bold green](current)[/]", str(msg_count), preview)
                else:
                    table.add_row(str(i), session_id, str(msg_count), preview)

            console.print(table)
        
        console.print("\n[dim]Use: /load <session_id> to switch sessions[/]")
        console.print("[dim]Use: /new to start a fresh session[/]\n")
        return True

    elif cmd == "new":
        # Start a new session
        old_session = agent.history.session_id
        new_agent = Agent(
            system_prompt=AGENT_CONFIG["system_prompt"],
            tools=AGENT_CONFIG["tools"],
            model=AGENT_CONFIG["model"],
            litellm_params=AGENT_CONFIG.get("litellm_params", {}),
        )
        console.print()
        console.print(f"[bold green]🆕 Started new session: {new_agent.history.session_id}[/]")
        console.print(f"[dim]Previous session: {old_session}[/]\n")
        return new_agent

    elif cmd == "load":
        if len(parts) == 1:
            console.print()
            console.print("[bold red]Usage: /load <session_id>[/]")
            console.print("[dim]Use /sessions to list available sessions[/]\n")
            return True
        
        session_id = parts[1]
        try:
            # Try to load the session
            old_session = agent.history.session_id
            new_agent = Agent(
                system_prompt=AGENT_CONFIG["system_prompt"],
                tools=AGENT_CONFIG["tools"],
                model=AGENT_CONFIG["model"],
                session_id=session_id,
                litellm_params=AGENT_CONFIG.get("litellm_params", {}),
            )
            
            console.print()
            console.print(f"[bold green]📂 Loaded session: {session_id}[/]")
            console.print(f"[dim]Previous session: {old_session}[/]")
            console.print(f"[dim]Loaded {len(new_agent.history.messages)} messages[/]")
            
            # Display the chat history
            load_and_display_chat_history(new_agent)
            
            return new_agent
        except Exception as e:
            console.print()
            console.print(f"[bold red]Failed to load session: {session_id}[/]")
            console.print(f"[dim]Error: {str(e)}[/]\n")
            return True

    elif cmd == "help":
        console.print()
        console.print("[bold cyan]📖 Prism Help[/]\n")
        console.print("[bold]Available Commands:[/]")
        
        # Show slash commands from config
        for cmd_name, desc in SLASH_COMMANDS:
            console.print(f"  [bold cyan]{cmd_name}[/] - {desc}")
        
        # Add session management commands
        console.print(f"  [bold cyan]/new[/] - Start new session")
        console.print(f"  [bold cyan]/load <session_id>[/] - Load a session")
        console.print(f"  [bold cyan]/theme <name>[/] - Change theme (run_fancy.py only)")
        console.print(f"  [bold cyan]/themes[/] - List all available themes")
        console.print(f"  [bold cyan]/toggle-diff[/] - Toggle detailed diff display")
        
        console.print(f"\n[bold]Keyboard Shortcuts:[/]")
        console.print(f"  [bold cyan]Ctrl+C[/] - Interrupt/Exit")
        console.print(f"  [bold cyan]quit, exit, q[/] - Exit application")
        
        console.print(f"\n[bold]Current Session:[/] {agent.history.session_id}")
        console.print(f"[bold]Model:[/] {agent.model.split('/')[-1]}")
        console.print(f"[bold]Tools:[/] {', '.join(t.__name__ for t in agent.tools)}")
        
        # Show settings
        settings = Settings()
        diff_status = "enabled" if settings.show_diff else "disabled"
        console.print(f"[bold]Detailed diffs:[/] {diff_status}")
        console.print()
        return True

    elif cmd == "session":
        if len(parts) == 1:
            # Show current session info
            console.print()
            console.print("[bold cyan]📋 Current Session[/]\n")
            console.print(f"  [dim]ID:[/] [bold cyan]{agent.history.session_id}[/]")
            console.print(f"  [dim]Messages:[/] {len(agent.history.messages)}")
            console.print(f"  [dim]Model:[/] {agent.model}")
            created = agent.history.metadata.get("created_at", "unknown")
            console.print(f"  [dim]Created:[/] {created}")
            console.print("\n[dim]Use /sessions to list all sessions[/]\n")
            return True

    return False


def show_session_picker():
    """Show session picker on startup. Returns session_id or None for new session."""
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
        choice = console.input("[bold yellow]>[/] ").strip()
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


def get_available_slash_commands():
    """Get all available slash commands with descriptions."""
    commands = []
    # Add commands from config
    for cmd, desc in SLASH_COMMANDS:
        commands.append((cmd, desc))
    
    # Add session management commands
    commands.extend([
        ("/new", "Start new session"),
        ("/load <session_id>", "Load a session"),
        ("/theme <name>", "Change theme (run_fancy.py only)"),
        ("/themes", "List all available themes"),
        ("/toggle-diff", "Toggle detailed diff display"),
    ])
    
    return commands


def show_command_suggestions(partial_input: str):
    """Show command suggestions for partial input."""
    if not partial_input.startswith("/"):
        return
    
    commands = get_available_slash_commands()
    matches = [(cmd, desc) for cmd, desc in commands if cmd.startswith(partial_input)]
    
    if matches:
        console.print()
        console.print("[dim]Available commands:[/]")
        for cmd, desc in matches:
            console.print(f"  [bold cyan]{cmd}[/] - {desc}")
        console.print()


def get_multiline_input() -> str:
    """Get user input, supporting multi-line input.

    - Single line input submits immediately on Enter
    - Use \\ at end of line for continuation
    - Triple-backtick code blocks (```...```) for multi-line
    """
    lines = []
    in_code_block = False

    try:
        while True:
            try:
                if not lines:
                    line = input()
                else:
                    line = input("  ")  # Indented continuation
            except (KeyboardInterrupt, EOFError):
                raise

            # Check for code block markers
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    lines.append(line)
                    continue
                else:
                    in_code_block = False
                    lines.append(line)
                    break  # End of code block, submit

            # If we're in a code block, keep collecting lines
            if in_code_block:
                lines.append(line)
                continue

            # Handle backslash continuation
            if line.endswith('\\'):
                lines.append(line[:-1])  # Remove backslash
                continue

            # Normal line - submit immediately
            lines.append(line)
            break

        result = '\n'.join(lines)
        return result.strip()

    except (KeyboardInterrupt, EOFError):
        raise


def main():
    import sys
    from config import get_agent_config

    session_id = None

    # Check for --new flag to skip session picker
    if "--new" not in sys.argv:
        session_id = show_session_picker()

    # Get fresh config to avoid NoneType/stale issues
    config = get_agent_config()

    agent = Agent(
        system_prompt=config["system_prompt"],
        tools=config["tools"],
        model=config["model"],
        session_id=session_id,
        litellm_params=config.get("litellm_params", {}),
    )

    # Rich welcome message
    welcome = Text()
    if agent.history.messages:
        welcome.append("📂 Session resumed!", style="bold green")
        welcome.append(f"\nLoaded {len(agent.history.messages)} messages", style="dim")
        welcome.append(f"\nSession: {agent.history.session_id[:8]}...", style="cyan")
        welcome.append(f"\nTools: {', '.join(t.__name__ for t in agent.tools)}", style="dim")
        welcome.append(f"\nModel: {agent.model.split('/')[-1]}", style="dim")
        welcome.append("\n\nType '/help' for commands, '/' + Tab for suggestions, or start chatting!\n", style="yellow")
        console.print(welcome)
        
        # Display the chat history
        load_and_display_chat_history(agent)
    else:
        welcome.append("Prism ready!", style="bold green")
        welcome.append(f"\nSession: {agent.history.session_id[:8]}...", style="cyan")
        welcome.append(f"\nTools: {', '.join(t.__name__ for t in agent.tools)}", style="dim")
        welcome.append(f"\nModel: {agent.model.split('/')[-1]}", style="dim")
        welcome.append("\n\nType '/help' for commands, '/' + Tab for suggestions, or start chatting!\n", style="yellow")
        console.print(welcome)

    while True:
        try:
            console.print("[bold yellow]You:[/] ", end="")
            user_input = get_multiline_input().strip()
            if user_input.lower() in ("quit", "exit", "q"):
                console.print("\n[bold yellow]Goodbye![/]")
                break

            if not user_input:
                continue

            # Show command suggestions if input starts with /
            if user_input == "/" or (user_input.startswith("/") and not user_input.endswith(" ")):
                show_command_suggestions(user_input)
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                result = handle_slash_command(agent, user_input)
                if result is True:
                    continue  # Command handled successfully
                elif isinstance(result, Agent):
                    agent = result  # New agent returned (session switch)
                    continue
                else:
                    console.print(f"\n[bold red]Unknown command: {user_input}[/]")
                    console.print("[dim]Type /help for available commands[/]\n")
                    continue

            print()
            run_agent_loop(agent, user_input)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Goodbye![/]")
            break


if __name__ == "__main__":
    main()
