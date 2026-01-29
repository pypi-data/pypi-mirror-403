"""Diff rendering for file edits."""
import difflib
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from config import LANG_MAP


class DiffRenderer:
    """Renders minimal unified diffs with syntax highlighting."""

    def __init__(self, theme_config: dict):
        self.theme_config = theme_config

    def create_minimal_diff(self, old_text: str, new_text: str, file_path: str) -> Panel | None:
        """Create a minimal compressed diff display with syntax highlighting."""
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        if old_lines == new_lines:
            return None

        # Detect language from file extension for syntax highlighting
        ext = file_path.split(".")[-1] if "." in file_path else "text"
        lang = LANG_MAP.get(ext, ext)

        # Create compact diff with syntax highlighting
        diff_parts = []
        changes_count = 0

        # Use unified diff but process it ourselves for better control
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=file_path, tofile=file_path,
            lineterm='', n=2  # Small amount of context
        ))

        if len(diff) <= 3:  # No changes beyond headers
            return None

        # Skip file headers and collect hunks
        i = 0
        while i < len(diff):
            line = diff[i]

            if line.startswith('@@'):
                # Hunk header
                diff_parts.append(("hunk", line))
                i += 1
                continue

            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                diff_parts.append(("remove", line[1:]))
                changes_count += 1

            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                diff_parts.append(("add", line[1:]))
                changes_count += 1

            elif line.startswith(' '):
                # Context line
                diff_parts.append(("context", line[1:]))

            i += 1

        if changes_count == 0:
            return None

        # Now render with syntax highlighting
        diff_content = Text()

        for part_type, content in diff_parts:
            if part_type == "hunk":
                # Hunk header - compact and themed
                diff_content.append("  ", style=self.theme_config["dim_color"])
                diff_content.append(content + "\n", style="bold " + self.theme_config["accent_color"])

            elif part_type == "remove":
                # Removed line with syntax highlighting
                diff_content.append("  ", style=self.theme_config["dim_color"])
                diff_content.append("- ", style="bold " + self.theme_config["error_color"])
                try:
                    # Apply syntax highlighting but keep the red theme
                    syntax = Syntax(content, lang, theme=self.theme_config["code_theme"],
                                    background_color=self.theme_config["remove_bg"])
                    diff_content.append(syntax)
                    diff_content.append("\n")
                except:
                    # Fallback to plain colored text
                    diff_content.append(content + "\n", style=self.theme_config["error_color"])

            elif part_type == "add":
                # Added line with syntax highlighting
                diff_content.append("  ", style=self.theme_config["dim_color"])
                diff_content.append("+ ", style="bold " + self.theme_config["success_color"])
                try:
                    # Apply syntax highlighting but keep the green theme
                    syntax = Syntax(content, lang, theme=self.theme_config["code_theme"],
                                    background_color=self.theme_config["add_bg"])
                    diff_content.append(syntax)
                    diff_content.append("\n")
                except:
                    # Fallback to plain colored text
                    diff_content.append(content + "\n", style=self.theme_config["success_color"])

            elif part_type == "context":
                # Context line with subtle syntax highlighting
                diff_content.append("  ", style=self.theme_config["dim_color"])
                diff_content.append("  ", style=self.theme_config["dim_color"])
                try:
                    # Very subtle syntax highlighting for context
                    syntax = Syntax(content, lang, theme=self.theme_config["code_theme"])
                    diff_content.append(syntax)
                    diff_content.append("\n")
                except:
                    # Fallback to dimmed text
                    diff_content.append(content + "\n", style=self.theme_config["dim_color"])

        # Create compact header with stats
        old_count = len(old_lines)
        new_count = len(new_lines)
        line_diff = new_count - old_count

        header_text = f"📝 {file_path}"
        if line_diff != 0:
            if line_diff > 0:
                header_text += f" (+{line_diff} lines)"
            else:
                header_text += f" ({line_diff} lines)"

        return Panel(
            diff_content,
            title=f"[{self.theme_config['tool_color']}]{header_text}[/]",
            border_style=self.theme_config["tool_color"],
            padding=(0, 1)
        )
