"""Autocomplete functionality for slash commands."""
from rich.text import Text
from textual.widgets import Static
from config import SLASH_COMMANDS


class AutocompleteManager:
    """Manages autocomplete state and rendering for slash commands."""

    def __init__(self, app):
        """Initialize with reference to the app for state access."""
        self.app = app
        self.show = False
        self.options: list[tuple[str, str]] = []
        self.selected = 0

    @property
    def theme_config(self):
        return self.app.theme_config

    def get_slash_commands(self) -> list[tuple[str, str]]:
        """Get available slash commands with descriptions."""
        return SLASH_COMMANDS + [
            ("/sessions", "List recent sessions"),
            ("/new", "Start new session"),
            ("/load <session_id>", "Load a session"),
        ]

    def update(self, text: str) -> None:
        """Update autocomplete suggestions based on current input."""
        if not text.startswith("/"):
            self.show = False
            return

        # Get matching commands
        commands = self.get_slash_commands()
        matches = [cmd for cmd, desc in commands if cmd.startswith(text)]

        if matches:
            self.options = [(cmd, desc) for cmd, desc in commands if cmd.startswith(text)]
            self.show = True
            self.selected = 0
        else:
            self.show = False

    def update_display(self) -> None:
        """Update the autocomplete display widget."""
        autocomplete_widget = self.app.query_one("#autocomplete", Static)

        if self.show and self.options:
            text = Text()
            for i, (cmd, desc) in enumerate(self.options):
                if i == self.selected:
                    text.append(f"► {cmd}", style="bold " + self.theme_config["accent_color"])
                    text.append(f" - {desc}\n", style="bold " + self.theme_config["text_color"])
                else:
                    text.append(f"  {cmd}", style=self.theme_config["tool_color"])
                    text.append(f" - {desc}\n", style=self.theme_config["dim_color"])

            autocomplete_widget.update(text)
            autocomplete_widget.add_class("show")
        else:
            autocomplete_widget.update("")
            autocomplete_widget.remove_class("show")

    def get_display_text(self) -> str:
        """Generate autocomplete display text (legacy method)."""
        if not self.show or not self.options:
            return ""

        lines = []
        for i, (cmd, desc) in enumerate(self.options):
            prefix = "► " if i == self.selected else "  "
            lines.append(f"{prefix}{cmd} - {desc}")

        return "\n".join(lines)

    def navigate_up(self) -> bool:
        """Navigate selection up. Returns True if handled."""
        if self.show and self.selected > 0:
            self.selected -= 1
            self.update_display()
            return True
        return False

    def navigate_down(self) -> bool:
        """Navigate selection down. Returns True if handled."""
        if self.show and self.selected < len(self.options) - 1:
            self.selected += 1
            self.update_display()
            return True
        return False

    def get_selected_command(self) -> str | None:
        """Get the currently selected command."""
        if self.show and self.options:
            return self.options[self.selected][0]
        return None

    def hide(self) -> None:
        """Hide the autocomplete."""
        self.show = False
        self.update_display()
