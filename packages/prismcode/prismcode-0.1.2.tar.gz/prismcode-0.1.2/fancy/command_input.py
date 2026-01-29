"""Command input bar widget with proper paste handling and command menu."""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.message import Message
from textual.events import Paste, Key
from textual import on

from .command_menu import CommandMenu


class CommandInputBar(Widget):
    """Bottom-docked input bar with command menu overlay.

    Features:
    - Single-line input with proper multi-line paste handling
    - Slash command autocomplete menu
    - Settings submenu
    - Keyboard navigation (up/down for menu, tab for completion)
    """

    DEFAULT_CSS = """
    CommandInputBar {
        dock: bottom;
        height: auto;
        width: 100%;
        layers: base menu;
    }

    CommandInputBar #input-container {
        width: 100%;
        height: auto;
        min-height: 1;
        layer: base;
    }

    CommandInputBar #prompt {
        width: 2;
        height: 1;
        content-align: right middle;
    }

    CommandInputBar #cmd-input {
        width: 1fr;
        height: auto;
        min-height: 1;
        border: none;
        padding: 0;
    }

    CommandInputBar #cmd-input:focus {
        border: none;
    }

    CommandInputBar CommandMenu {
        width: 100%;
        layer: menu;
    }
    """

    # Messages
    class Submitted(Message):
        """Fired when input is submitted."""
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    class InputChanged(Message):
        """Fired when input changes."""
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    # State
    processing = reactive(False)

    def __init__(self, theme_config: dict, **kwargs):
        super().__init__(**kwargs)
        self.theme_config = theme_config
        self._pending_paste: str | None = None

    def compose(self) -> ComposeResult:
        yield CommandMenu(self.theme_config, id="command-menu")
        with Horizontal(id="input-container"):
            yield Static("> ", id="prompt")
            yield Input(id="cmd-input", placeholder="")

    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one("#cmd-input", Input).focus()

    @property
    def value(self) -> str:
        """Get current input value."""
        return self.query_one("#cmd-input", Input).value

    @value.setter
    def value(self, text: str) -> None:
        """Set input value."""
        self.query_one("#cmd-input", Input).value = text

    def focus_input(self) -> None:
        """Focus the input widget."""
        self.query_one("#cmd-input", Input).focus()

    def clear(self) -> None:
        """Clear the input."""
        self.query_one("#cmd-input", Input).value = ""
        menu = self.query_one("#command-menu", CommandMenu)
        if menu.visible:
            menu.hide()

    # Paste handling - the key fix for multi-line paste
    def on_paste(self, event: Paste) -> None:
        """Handle paste events - this is the fix for multi-line paste.

        Instead of letting each line trigger a submit, we capture the entire
        paste content and insert it as a single value.
        """
        event.stop()  # Prevent default handling

        input_widget = self.query_one("#cmd-input", Input)

        # Get pasted text - normalize line endings and join with spaces
        # (since this is a single-line input, we convert newlines to spaces)
        pasted = event.text
        if pasted:
            # For a command input, replace newlines with spaces
            # This allows pasting multi-line content without triggering multiple submits
            normalized = pasted.replace('\r\n', '\n').replace('\r', '\n')

            # Option 1: Replace newlines with spaces (single-line mode)
            single_line = normalized.replace('\n', ' ').strip()

            # Insert at cursor position
            current = input_widget.value
            # For simplicity, append to end (Input widget handles cursor internally)
            input_widget.value = current + single_line if current else single_line

            # Move cursor to end
            input_widget.cursor_position = len(input_widget.value)

    @on(Input.Changed, "#cmd-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for autocomplete."""
        event.stop()
        text = event.value
        menu = self.query_one("#command-menu", CommandMenu)

        # Show menu when typing slash commands
        if text.startswith("/"):
            menu.show(text)
        elif menu.visible and not menu.in_settings:
            menu.hide()

        self.post_message(self.InputChanged(text))

    @on(Input.Submitted, "#cmd-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        event.stop()

        menu = self.query_one("#command-menu", CommandMenu)

        # If menu is visible and has selection, select it instead of submitting
        if menu.visible:
            menu.select_current()
            return

        text = event.value.strip()
        if text and not self.processing:
            self.post_message(self.Submitted(text))

    def on_key(self, event: Key) -> None:
        """Handle keyboard navigation."""
        menu = self.query_one("#command-menu", CommandMenu)
        input_widget = self.query_one("#cmd-input", Input)

        # Handle menu navigation when menu is visible
        if menu.visible:
            if event.key == "up":
                if menu.navigate_up():
                    event.stop()
                    event.prevent_default()
                return

            if event.key == "down":
                if menu.navigate_down():
                    event.stop()
                    event.prevent_default()
                return

            if event.key == "tab":
                # Tab completion - get selected command and fill input
                option_list = menu.query_one("#command-list")
                if option_list.highlighted is not None:
                    try:
                        option = option_list.get_option_at_index(option_list.highlighted)
                        if option and option.id and str(option.id).startswith("/"):
                            input_widget.value = str(option.id) + " "
                            input_widget.cursor_position = len(input_widget.value)
                            menu.hide()
                    except Exception:
                        pass
                event.stop()
                event.prevent_default()
                return

            if event.key == "escape":
                menu.hide()
                input_widget.focus()
                event.stop()
                event.prevent_default()
                return

        # Ctrl+C handling
        if event.key == "ctrl+c":
            if input_widget.value:
                input_widget.value = ""
                event.stop()
                event.prevent_default()

    @on(CommandMenu.CommandSelected)
    def on_command_selected(self, event: CommandMenu.CommandSelected) -> None:
        """Handle command selection from menu."""
        event.stop()
        input_widget = self.query_one("#cmd-input", Input)

        # Fill in the command
        cmd = event.command
        if " " not in cmd:  # Simple command, add space for args
            input_widget.value = cmd + " "
        else:
            input_widget.value = cmd

        input_widget.cursor_position = len(input_widget.value)
        input_widget.focus()

    @on(CommandMenu.SettingChanged)
    def on_setting_changed(self, event: CommandMenu.SettingChanged) -> None:
        """Bubble setting changes up to the app."""
        # Just let it bubble - app will handle it
        pass

    @on(CommandMenu.Dismissed)
    def on_menu_dismissed(self, event: CommandMenu.Dismissed) -> None:
        """Handle menu dismissal."""
        event.stop()
        self.query_one("#cmd-input", Input).focus()

    def update_theme(self, theme_config: dict) -> None:
        """Update theme configuration."""
        self.theme_config = theme_config
        self.query_one("#command-menu", CommandMenu).update_theme(theme_config)

    def show_menu(self, filter_text: str = "") -> None:
        """Programmatically show the command menu."""
        self.query_one("#command-menu", CommandMenu).show(filter_text)

    def hide_menu(self) -> None:
        """Programmatically hide the command menu."""
        self.query_one("#command-menu", CommandMenu).hide()
