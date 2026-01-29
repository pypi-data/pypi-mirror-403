"""Main Prism TUI application."""from textual.app import App, ComposeResult
from textual.containers import Vertical, ScrollableContainer
from textual.widgets import Static, Input
from textual.binding import Binding
from textual import work, on

from core.agent import Agent
from themes import THEMES
from settings import Settings
from config import AGENT_CONFIG

from .css import generate_css
from .commands import SlashCommandHandler
from .scroll import ScrollManager
from .agent_runner import AgentRunner
from .chat_renderer import ChatRenderer
from .command_input import CommandInputBar
from .command_menu import CommandMenu
from .focus_bar import FocusBar


class PrismApp(App):
    """Main Prism TUI application."""

    TITLE = "Prism"    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "cancel", "Stop", show=True),
        Binding("end", "scroll_bottom", "Bottom", show=True),
    ]

    def __init__(self, theme_name: str = "default", session_id: str = None):
        # ansi_color=True enables terminal transparency
        super().__init__(ansi_color=True)

        # Load settings
        self.settings = Settings()

        # Use saved theme if available, otherwise use provided theme
        self.theme_name = self.settings.theme if self.settings.theme in THEMES else theme_name
        self.theme_config = THEMES[self.theme_name]
        self.CSS = generate_css(self.theme_config)

        self.agent = Agent(
            system_prompt=AGENT_CONFIG["system_prompt"],
            tools=AGENT_CONFIG["tools"],
            model=AGENT_CONFIG["model"],
            session_id=session_id,
        )
        self.processing = False
        self.cancelled = False
        self.current_stream = ""  # Current streaming text
        self.messages = []  # Chat messages
        self.queued_message = None  # Message queued to send after current completes

        # Initialize component managers
        self.command_handler = SlashCommandHandler(self)
        self.scroll_manager = ScrollManager(self)
        self.agent_runner = AgentRunner(self)
        self.chat_renderer = ChatRenderer(self)

    def save_settings(self):
        """Save current settings."""
        self.settings.theme = self.theme_name
        self.settings.save()

    def set_theme(self, theme_name: str) -> bool:
        """Change the current theme."""
        if theme_name in THEMES:
            self.theme_name = theme_name
            self.theme_config = THEMES[theme_name]
            self.CSS = generate_css(self.theme_config)
            self.refresh_css()
            self.save_settings()
            # Update agent runner's diff renderer theme
            self.agent_runner.update_theme(self.theme_config)
            # Update command input bar theme
            try:
                self.query_one(CommandInputBar).update_theme(self.theme_config)
            except Exception:
                pass
            # Update focus bar theme
            try:
                self.query_one(FocusBar).update_theme(self.theme_config)
            except Exception:
                pass
            return True
        return False

    def get_slash_commands(self):
        """Get available slash commands with descriptions."""
        from config import SLASH_COMMANDS
        return SLASH_COMMANDS + [
            ("/sessions", "List recent sessions"),
            ("/new", "Start new session"),
            ("/load <session_id>", "Load a session"),
            ("/settings", "Open settings menu"),
        ]

    def _add_message(self, msg):
        """Helper to add a message and refresh chat."""
        self.messages.append(msg)
        self._refresh_chat()
        self._focus_input()

    def _focus_input(self):
        """Focus the command input."""
        try:
            self.query_one(CommandInputBar).focus_input()
        except Exception:
            pass

    def _refresh_focus_bar(self):
        """Refresh the focus bar display."""
        try:
            self.query_one(FocusBar).refresh_display()
        except Exception:
            pass

    def _load_chat_history(self):
        """Load session history into display messages."""
        self.chat_renderer.load_chat_history()

    def _refresh_chat(self):
        """Re-render the entire chat."""
        self.chat_renderer.refresh()

    def _throttled_refresh(self):
        """Throttled refresh for smooth streaming."""
        self.chat_renderer.throttled_refresh()

    def _status_text(self, extra: str = "") -> str:
        """Generate status bar text."""
        base = f" {self.agent.history.session_id[:8]}   {len(self.agent.tools)} tools   {self.agent.model.split('/')[-1]}"

        # Add scroll indicator if user has scrolled up
        if self.scroll_manager.user_scrolled_up and not self.scroll_manager.auto_scroll:
            scroll_indicator = "  auto-scroll OFF (End to resume)"
            base += scroll_indicator

        return f"{base}  {extra}" if extra else base

    def compose(self) -> ComposeResult:
        with Vertical(id="main"):
            with ScrollableContainer(id="chat-scroll"):
                yield Static("", id="chat-content")
            yield FocusBar(self.theme_config, self.agent.history.session_id, id="focus-bar")
            yield Static(self._status_text(), id="status")
        yield CommandInputBar(self.theme_config, id="command-bar")

    def on_mount(self) -> None:
        """Handle app mount."""
        # Check if we loaded an existing session with messages
        if self.agent.history.messages:
            self._load_chat_history()
            self.messages.append(self.chat_renderer.create_resumed_message())
        else:
            self.messages.append(self.chat_renderer.create_welcome_message())

        self._refresh_chat()
        self._focus_input()

        # Set up scroll event monitoring
        scroll_container = self.query_one("#chat-scroll", ScrollableContainer)
        scroll_container.can_focus = True

    def on_scroll_view_scroll(self, event) -> None:
        """Handle scroll events."""
        self.scroll_manager.handle_scroll_event(event)

    def on_key(self, event) -> None:
        """Handle key events."""
        # Handle Ctrl+C: clear input if has text, otherwise quit
        if event.key == "ctrl+c":
            try:
                cmd_bar = self.query_one(CommandInputBar)
                if cmd_bar.value.strip():
                    cmd_bar.clear()
                else:
                    self.exit()
            except Exception:
                self.exit()
            event.prevent_default()
            return

        # Handle scroll keys when not in input
        if event.key in ("pageup", "pagedown", "home"):
            self.call_later(self.scroll_manager.check_scroll_position)

    # Handle CommandInputBar messages

    @on(CommandInputBar.Submitted)
    def on_command_submitted(self, event: CommandInputBar.Submitted) -> None:
        """Handle input submission from command bar."""
        event.stop()
        self._submit_input(event.value)

    @on(CommandMenu.SettingChanged)
    def on_setting_changed(self, event: CommandMenu.SettingChanged) -> None:
        """Handle setting changes from command menu."""
        event.stop()

        if event.setting == "theme":
            if self.set_theme(event.value):
                from rich.text import Text
                msg = Text()
                msg.append(f"\nTheme changed to: {self.theme_config['name']}", style=self.theme_config["success_color"])
                self._add_message(msg)
            else:
                from rich.text import Text
                msg = Text()
                msg.append(f"\nUnknown theme: {event.value}", style=self.theme_config["error_color"])
                self._add_message(msg)

        elif event.setting == "toggle_diff":
            self.settings.show_diff = not self.settings.show_diff
            self.save_settings()
            from rich.text import Text
            status = "enabled" if self.settings.show_diff else "disabled"
            msg = Text()
            msg.append(f"\nDetailed diff display {status}", style=self.theme_config["success_color"])
            self._add_message(msg)

    # Actions

    def action_scroll_bottom(self) -> None:
        """Scroll to bottom and re-enable auto-scroll."""
        self.scroll_manager.force_scroll_to_bottom()
        if not self.processing:
            self.query_one("#status", Static).update(self._status_text())

    def action_cancel(self) -> None:
        """Cancel current generation with Escape."""
        if self.processing:
            self.cancelled = True
            self.queued_message = None  # Clear any queued message
            # Commit partial stream with cancelled marker
            if self.current_stream:
                self.messages.append(self.chat_renderer.create_cancelled_message(self.current_stream))
                self.current_stream = ""
            self._refresh_chat()
            self.query_one("#status", Static).update(self._status_text())

    def _submit_input(self, text: str) -> None:
        """Submit input text.
        
        Behavior:
        - If not processing: send immediately
        - If processing + no queued message: queue it (will send when done)
        - If processing + already queued: interrupt and send immediately
        """
        if not text:
            return

        if self.processing:
            if self.queued_message is None:
                # First enter while processing: queue the message
                self.queued_message = text
                self.query_one("#status", Static).update(
                    self._status_text(f"queued: {text[:30]}{'...' if len(text) > 30 else ''} (enter again to interrupt)")
                )
                # Clear the input
                try:
                    self.query_one(CommandInputBar).clear()
                except Exception:
                    pass
                return
            else:
                # Second enter: interrupt and send
                self.cancelled = True
                # The queued message will be replaced by new text
                self.queued_message = text
                # Clear the input
                try:
                    self.query_one(CommandInputBar).clear()
                except Exception:
                    pass
                # Commit partial stream with cancelled marker
                if self.current_stream:
                    self.messages.append(self.chat_renderer.create_cancelled_message(self.current_stream))
                    self.current_stream = ""
                self._refresh_chat()
                self.query_one("#status", Static).update(self._status_text("interrupting..."))
                return

        # Clear the input
        try:
            self.query_one(CommandInputBar).clear()
        except Exception:
            pass

        if text.lower() in ("quit", "exit", "q"):
            self.exit()
            return

        # Handle slash commands
        if text.startswith("/"):
            # Handle /settings specially - it's handled by the menu
            if text.strip() == "/settings":
                try:
                    self.query_one(CommandInputBar).show_menu("/")
                except Exception:
                    pass
                return

            if self.command_handler.handle(text):
                return
            else:
                self.messages.append(self.chat_renderer.create_error_message(text))
                self._refresh_chat()
                self._focus_input()
                return

        self.processing = True
        self.cancelled = False

        # Add user message
        self.messages.append(self.chat_renderer.create_user_message(text))

        # Force scroll to bottom when user sends a message
        self.scroll_manager.force_scroll_to_bottom()
        self._refresh_chat()

        self.query_one("#status", Static).update(self._status_text("streaming..."))
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, user_input: str) -> None:
        """Run agent in background thread."""
        self.agent_runner.run(user_input)
