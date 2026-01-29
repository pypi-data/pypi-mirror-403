"""Command menu widget with slash commands and settings submenus."""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical, Container
from textual.reactive import reactive
from textual.message import Message
from textual import on
from rich.text import Text

from config import SLASH_COMMANDS


class CommandMenu(Widget):
    """Animated dropdown menu for slash commands and settings."""

    DEFAULT_CSS = """
    CommandMenu {
        height: auto;
        max-height: 12;
        display: none;
        layer: menu;
    }

    CommandMenu.visible {
        display: block;
    }

    CommandMenu OptionList {
        height: auto;
        max-height: 10;
        border: none;
        padding: 0 1;
        scrollbar-size: 1 1;
    }

    CommandMenu OptionList:focus {
        border: none;
    }

    CommandMenu .settings-panel {
        display: none;
        height: auto;
        max-height: 10;
        padding: 0 1;
    }

    CommandMenu .settings-panel.visible {
        display: block;
    }
    """

    # Messages
    class CommandSelected(Message):
        """Fired when a command is selected."""
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    class SettingChanged(Message):
        """Fired when a setting is changed."""
        def __init__(self, setting: str, value: any) -> None:
            self.setting = setting
            self.value = value
            super().__init__()

    class Dismissed(Message):
        """Fired when menu is dismissed."""
        pass

    # State
    visible = reactive(False)
    filter_text = reactive("")
    in_settings = reactive(False)
    settings_section = reactive("")  # "", "theme", "model"

    def __init__(self, theme_config: dict, **kwargs):
        super().__init__(**kwargs)
        self.theme_config = theme_config
        self._all_commands = self._build_command_list()
        self._mounted = False  # Guard against refresh before mount
        self._refreshing = False  # Reentrancy guard

    def _build_command_list(self) -> list[tuple[str, str]]:
        """Build list of all available commands."""
        # Start with SLASH_COMMANDS from config, then add extras that aren't duplicates
        commands = list(SLASH_COMMANDS)
        existing_cmds = {cmd for cmd, _ in commands}

        extras = [
            ("/new", "Start new session"),
            ("/load <id>", "Load a session"),
            ("/settings", "Open settings menu"),
        ]

        for cmd, desc in extras:
            if cmd not in existing_cmds:
                commands.append((cmd, desc))

        return commands

    def compose(self) -> ComposeResult:
        with Vertical():
            yield OptionList(id="command-list")
            yield Container(id="settings-panel", classes="settings-panel")

    def on_mount(self) -> None:
        """Initialize the option list."""
        self._mounted = True
        self._refresh_options()

    def _refresh_options(self) -> None:
        """Refresh the option list based on current filter."""
        if not self._mounted or self._refreshing:
            return  # Don't refresh before mount or if already refreshing

        self._refreshing = True
        try:
            option_list = self.query_one("#command-list", OptionList)
            option_list.clear_options()

            if self.in_settings:
                self._populate_settings_options(option_list)
            else:
                self._populate_command_options(option_list)
        finally:
            self._refreshing = False

    def _populate_command_options(self, option_list: OptionList) -> None:
        """Populate with filtered slash commands."""
        filter_lower = self.filter_text.lower()

        for cmd, desc in self._all_commands:
            if filter_lower and not cmd.lower().startswith(filter_lower):
                continue

            # Create styled option
            text = Text()
            text.append(cmd, style="bold " + self.theme_config.get("tool_color", "cyan"))
            text.append(f"  {desc}", style=self.theme_config.get("dim_color", "dim"))
            option_list.add_option(Option(text, id=cmd))

    def _populate_settings_options(self, option_list: OptionList) -> None:
        """Populate with settings options."""
        if self.settings_section == "":
            # Main settings menu
            options = [
                ("theme", "Change theme"),
                ("diff", "Toggle diff display"),
                ("back", "Back to commands"),
            ]
            for opt_id, label in options:
                text = Text()
                if opt_id == "back":
                    text.append(" Back", style="dim italic")
                else:
                    text.append(f" {label}", style=self.theme_config.get("text_color", "white"))
                option_list.add_option(Option(text, id=f"settings:{opt_id}"))

        elif self.settings_section == "theme":
            # Theme submenu
            from themes import THEMES
            text = Text()
            text.append(" Back", style="dim italic")
            option_list.add_option(Option(text, id="settings:back"))

            # Add a visual separator using a disabled option
            sep_text = Text("───────────", style="dim")
            option_list.add_option(Option(sep_text, id="sep", disabled=True))

            for theme_name in THEMES.keys():
                theme = THEMES[theme_name]
                text = Text()
                text.append(f"  {theme_name}", style="bold " + theme.get("user_color", "blue"))
                text.append(f"  {theme.get('name', '')}", style=theme.get("dim_color", "dim"))
                option_list.add_option(Option(text, id=f"theme:{theme_name}"))

    def watch_visible(self, visible: bool) -> None:
        """Handle visibility changes."""
        if visible:
            self.add_class("visible")
            self._refresh_options()
            # Focus the option list and highlight first item
            option_list = self.query_one("#command-list", OptionList)
            option_list.focus()
            if option_list.option_count > 0:
                option_list.highlighted = 0
        else:
            self.remove_class("visible")
            self.in_settings = False
            self.settings_section = ""
            self.filter_text = ""

    def watch_filter_text(self, text: str) -> None:
        """Handle filter text changes."""
        if self._mounted and not self.in_settings:
            self._refresh_options()

    def watch_in_settings(self, in_settings: bool) -> None:
        """Handle settings mode changes."""
        if self._mounted:
            self._refresh_options()

    def watch_settings_section(self, section: str) -> None:
        """Handle settings section changes."""
        if self._mounted and self.in_settings:
            self._refresh_options()

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        event.stop()
        option_id = str(event.option_id)

        if option_id.startswith("settings:"):
            action = option_id.split(":", 1)[1]
            if action == "back":
                if self.settings_section:
                    self.settings_section = ""
                else:
                    self.in_settings = False
                    self._refresh_options()
            elif action == "theme":
                self.settings_section = "theme"
            elif action == "diff":
                self.post_message(self.SettingChanged("toggle_diff", None))
                self.visible = False
        elif option_id.startswith("theme:"):
            theme_name = option_id.split(":", 1)[1]
            self.post_message(self.SettingChanged("theme", theme_name))
            self.visible = False
        elif option_id.startswith("/"):
            if option_id == "/settings":
                self.in_settings = True
            else:
                self.post_message(self.CommandSelected(option_id))
                self.visible = False

    def show(self, filter_text: str = "") -> None:
        """Show the menu with optional filter."""
        self.filter_text = filter_text
        self.visible = True

    def hide(self) -> None:
        """Hide the menu."""
        self.visible = False
        self.post_message(self.Dismissed())

    def update_theme(self, theme_config: dict) -> None:
        """Update theme configuration."""
        self.theme_config = theme_config
        if self.visible:
            self._refresh_options()

    def navigate_up(self) -> bool:
        """Navigate selection up. Returns True if handled."""
        if self.visible:
            option_list = self.query_one("#command-list", OptionList)
            if option_list.option_count == 0:
                return False
            if option_list.highlighted is None:
                option_list.highlighted = 0
            elif option_list.highlighted > 0:
                option_list.highlighted -= 1
            return True
        return False

    def navigate_down(self) -> bool:
        """Navigate selection down. Returns True if handled."""
        if self.visible:
            option_list = self.query_one("#command-list", OptionList)
            if option_list.option_count == 0:
                return False
            if option_list.highlighted is None:
                option_list.highlighted = 0
            elif option_list.highlighted < option_list.option_count - 1:
                option_list.highlighted += 1
            return True
        return False

    def select_current(self) -> bool:
        """Select the current option. Returns True if handled."""
        if self.visible:
            option_list = self.query_one("#command-list", OptionList)
            option_list.action_select()
            return True
        return False
