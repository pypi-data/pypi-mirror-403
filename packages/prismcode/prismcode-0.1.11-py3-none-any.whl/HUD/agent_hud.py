# -*- coding: utf-8 -*-
"""
Agent HUD - Heads-Up Display for real-time agent stats and context.

Shows:
- Current model
- Session ID
- Token counts (total, working history)
- Entry counts (ground truth, working, user/assistant/tool breakdown)
- Active projection info
- Recent tool usage
- Project file tree
"""

from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
import time

from HUD.file_tree import FileTree, get_file_tree_for_project
from HUD.focus_tree import FocusTree


class AgentHUD:
    """Real-time HUD for agent stats."""

    def __init__(self, agent):
        """
        Args:
            agent: The Agent instance to monitor
        """
        self.agent = agent
        self.console = Console()
        self.start_time = time.time()

    def _get_stats_panel(self) -> Panel:
        """Build the stats panel."""
        try:
            stats = self.agent.get_stats()
        except Exception as e:
            # Fallback if stats fail
            stats = {
                "ground_truth_entries": 0,
                "working_entries": 0,
                "gists": 0,
                "ground_truth_tokens": 0,
                "working_tokens": 0,
            }

        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")

        # Session info
        session_id = getattr(self.agent.history, "session_id", "unknown")
        if len(session_id) > 8:
            session_id = session_id[:8] + "..."

        table.add_row("Session ID", session_id)
        table.add_row("Model", str(self.agent.model))
        table.add_row("Uptime", f"{int(time.time() - self.start_time)}s")
        table.add_row("", "")

        # Entry counts
        table.add_row("Ground Truth", f"{stats.get('ground_truth_entries', 0)} entries")
        table.add_row("Working History", f"{stats.get('working_entries', 0)} entries")
        table.add_row("Gists", str(stats.get("gists", 0)))
        table.add_row("", "")

        # Token counts
        table.add_row("GT Tokens", f"{stats.get('ground_truth_tokens', 0):,}")
        table.add_row("Working Tokens", f"{stats.get('working_tokens', 0):,}")

        return Panel(table, title="[bold cyan]Agent Stats[/bold cyan]", border_style="cyan")

    def _get_projection_panel(self) -> Panel:
        """Build the projection info panel."""
        # Get projection details from history manager
        proj = self.agent.history_manager.projection

        info = Text()
        info.append("Active Projections:\n", style="bold yellow")

        # Parse projection info (this is simplified - actual implementation depends on projection structure)
        if hasattr(proj, "__name__"):
            info.append(f"  • {proj.__name__}\n", style="green")
        else:
            info.append("  • dedupe_file_reads\n", style="green")
            info.append("  • keep_recent_tool_results(30)\n", style="green")

        return Panel(info, title="[bold yellow]Context Management[/bold yellow]", border_style="yellow")

    def _get_recent_tools_panel(self) -> Panel:
        """Build recent tool usage panel."""
        stats = self.agent.get_stats()

        table = Table.grid(padding=(0, 1))
        table.add_column(style="magenta", justify="right")
        table.add_column(style="white")

        # Show files that have been read
        files = stats.get("files_read", [])[:5]
        if files:
            table.add_row("Files:", "")
            for f in files:
                short = f.split("/")[-1] if "/" in f else f
                table.add_row("", f"• {short}")

        # Show tools used
        tools = stats.get("tools_used", [])
        if tools:
            table.add_row("", "")
            table.add_row("Tools:", ", ".join(tools))

        return Panel(
            table,
            title="[bold magenta]Context Usage[/bold magenta]",
            border_style="magenta",
        )

    def _get_focus_tree_panel(self) -> Panel:
        """Build the dependency-aware focus tree panel."""
        try:
            from tools.prism_tools import _get_prism_session, _get_focused_files
            session = _get_prism_session()
            focused_files = _get_focused_files()
            
            if not focused_files:
                return Panel(Text("(No files focused)", style="dim"), title="[bold blue]Focus Deps[/bold blue]", border_style="blue")
                
            tree_gen = FocusTree(session)
            tree_text = tree_gen.generate(focused_files)
            
            return Panel(
                Text(tree_text, style="blue"),
                title="[bold blue]Focus Deps[/bold blue]",
                border_style="blue",
            )
        except Exception as e:
            return Panel(Text(f"Error: {e}", style="red"), title="[bold blue]Focus Deps[/bold blue]", border_style="blue")

    def _get_file_tree_panel(self) -> Panel:
        """Build the file tree panel."""
        tree_text = get_file_tree_for_project()

        # Truncate if too long
        lines = tree_text.split("\n")
        if len(lines) > 25:
            tree_text = "\n".join(lines[:25]) + f"\n... ({len(lines) - 25} more lines)"

        return Panel(
            Text(tree_text, style="dim green"),
            title="[bold green]Project Tree[/bold green]",
            border_style="green",
        )

    def render(self) -> Layout:
        """Render the full HUD layout."""
        layout = Layout()

        layout.split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        layout["left"].split_column(
            Layout(self._get_stats_panel(), name="stats", size=17),
            Layout(self._get_projection_panel(), name="projection", size=8),
            Layout(self._get_recent_tools_panel(), name="tools", size=10),
        )

        layout["right"].split_column(
            Layout(self._get_focus_tree_panel(), name="focus", size=15),
            Layout(self._get_file_tree_panel(), name="tree"),
        )

        return layout

    def display(self):
        """Display the HUD once (static)."""
        self.console.print(self.render())

    def to_markdown(self) -> str:
        """Render HUD as markdown."""
        try:
            stats = self.agent.get_stats()
        except Exception:
            stats = {
                "ground_truth_entries": 0,
                "working_entries": 0,
                "gists": 0,
                "ground_truth_tokens": 0,
                "working_tokens": 0,
                "files_read": [],
                "tools_used": [],
            }

        md = "# Agent HUD\n\n"

        # Stats section
        md += "## Stats\n\n"
        session_id = getattr(self.agent.history, "session_id", "unknown")[:8]
        md += f"- **Session ID**: {session_id}...\n"
        md += f"- **Model**: {self.agent.model}\n"
        md += f"- **Uptime**: {int(time.time() - self.start_time)}s\n"
        md += f"- **Ground Truth**: {stats.get('ground_truth_entries', 0)} entries\n"
        md += f"- **Working History**: {stats.get('working_entries', 0)} entries\n"
        md += f"- **Gists**: {stats.get('gists', 0)}\n"
        md += f"- **GT Tokens**: {stats.get('ground_truth_tokens', 0):,}\n"
        md += f"- **Working Tokens**: {stats.get('working_tokens', 0):,}\n\n"

        # Focus Dependency Tree
        md += "## Focus Dependency Tree\n\n"
        try:
            from tools.prism_tools import _get_prism_session, _get_focused_files
            session = _get_prism_session()
            focused_files = _get_focused_files()
            if focused_files:
                tree_gen = FocusTree(session)
                md += "```\n"
                md += tree_gen.generate(focused_files)
                md += "\n```\n\n"
            else:
                md += "(No files focused)\n\n"
        except Exception as e:
            md += f"(Error generating focus tree: {e})\n\n"

        # File tree
        md += "## Project Tree\n\n"
        md += "```\n"
        md += get_file_tree_for_project()
        md += "\n```\n\n"

        # Projection section
        md += "## Context Management\n\n"
        md += "Active Projections:\n"
        md += "- dedupe_file_reads\n"
        md += "- keep_recent_tool_results(30)\n\n"

        # Context usage
        md += "## Context Usage\n\n"
        files = stats.get("files_read", [])
        if files:
            md += "**Files Read**:\n"
            for f in files[:10]:
                md += f"- `{f}`\n"
            md += "\n"

        tools = stats.get("tools_used", [])
        if tools:
            md += f"**Tools Used**: {', '.join(tools)}\n\n"

        # Working history snapshot
        md += "## Working History Messages\n\n"
        try:
            entries = self.agent.history_manager.working.entries[-10:]
            for i, entry in enumerate(entries, 1):
                role = entry.role
                content = entry.content or ""
                if entry.tool_calls:
                    tool_names = [tc["function"]["name"] for tc in entry.tool_calls]
                    md += f"{i}. **{role}** (tools: {', '.join(tool_names)})\n"
                elif role == "tool":
                    tool_name = entry.meta.get("tool_name", "unknown")
                    md += f"{i}. **{role}** ({tool_name}): {content[:100]}...\n"
                else:
                    preview = content[:100].replace("\n", " ")
                    md += f"{i}. **{role}**: {preview}{'...' if len(content) > 100 else ''}\n"
        except Exception:
            md += "(No messages yet)\n"

        return md

    def save_markdown(self, path: str = "hud_output.md"):
        """Save HUD to markdown file."""
        with open(path, "w") as f:
            f.write(self.to_markdown())

    def live(self, refresh_rate: float = 1.0, save_md: Optional[str] = None):
        """
        Display the HUD with live updates.

        Args:
            refresh_rate: Update frequency in seconds
            save_md: If provided, save markdown output to this file on each update
        """
        with Live(self.render(), console=self.console, refresh_per_second=1 / refresh_rate) as live:
            try:
                while True:
                    time.sleep(refresh_rate)
                    live.update(self.render())
                    if save_md:
                        self.save_markdown(save_md)
            except KeyboardInterrupt:
                pass


def demo():
    """Demo the HUD with a real agent."""
    import sys
    sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

    from core.agent import Agent
    from tools.tools import read_file, create_file, edit_file

    agent = Agent(
        system_prompt="You are a helpful coding assistant.",
        tools=[read_file, create_file, edit_file],
        model="gpt-4o-mini",
    )

    hud = AgentHUD(agent)

    # Static display
    print("\n=== Agent HUD Demo ===\n")
    hud.display()

    # Save markdown
    print("\nSaving to hud_output.md...")
    hud.save_markdown("hud_output.md")

    # Uncomment for live updates with markdown output:
    # hud.live(refresh_rate=2.0, save_md="hud_output.md")


if __name__ == "__main__":
    demo()
