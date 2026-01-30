"""Slash command handling for Prism TUI."""from rich.text import Text
from themes import THEMES
from config import AGENT_CONFIG


class SlashCommandHandler:
    """Handles all slash commands for the TUI."""

    def __init__(self, app):
        """Initialize with reference to the app for state access."""
        self.app = app

    @property
    def theme_config(self):
        return self.app.theme_config

    def handle(self, command: str) -> bool:
        """Handle slash commands. Returns True if command was handled."""
        parts = command[1:].split()  # Remove leading slash
        if not parts:
            return False

        cmd = parts[0].lower()

        handlers = {
            "theme": self._handle_theme,
            "themes": self._handle_themes,
            "toggle-diff": self._handle_toggle_diff,
            "diff": self._handle_toggle_diff,
            "sessions": self._handle_sessions,
            "new": self._handle_new,
            "load": self._handle_load,
            "help": self._handle_help,
            "session": self._handle_session,
        }

        handler = handlers.get(cmd)
        if handler:
            return handler(parts)
        return False

    def _handle_theme(self, parts: list) -> bool:
        """Handle /theme command."""
        if len(parts) == 1:
            # List available themes
            themes_list = ", ".join(THEMES.keys())
            current = self.theme_config["name"]
            msg = Text()
            msg.append(f"\nAvailable themes: {themes_list}\n", style=self.theme_config["dim_color"])
            msg.append(f"Current theme: {current}", style=self.theme_config["accent_color"])
            self.app._add_message(msg)
            return True

        elif len(parts) == 2:
            theme_name = parts[1]
            if self.app.set_theme(theme_name):
                msg = Text()
                msg.append(f"\nTheme changed to: {self.theme_config['name']}", style=self.theme_config["success_color"])
                self.app._add_message(msg)
                return True
            else:
                msg = Text()
                msg.append(f"\nUnknown theme: {theme_name}", style=self.theme_config["error_color"])
                available = ", ".join(THEMES.keys())
                msg.append(f"\nAvailable themes: {available}", style=self.theme_config["dim_color"])
                self.app._add_message(msg)
                return True

        return False

    def _handle_themes(self, parts: list) -> bool:
        """Handle /themes command - show available themes."""
        msg = Text()
        msg.append("\nThemes\n\n", style="bold " + self.theme_config["accent_color"])

        for name, theme in THEMES.items():
            current_marker = " ✓" if name == self.app.theme_name else ""
            msg.append(f"  {name:15}", style="bold " + theme["user_color"])
            msg.append(f" {theme['name']}", style=theme["text_color"])
            msg.append(f"{current_marker}\n", style="bold " + self.theme_config["success_color"])

        msg.append(f"\n/theme <name> to switch\n", style=self.theme_config["dim_color"])

        self.app._add_message(msg)
        return True

    def _handle_toggle_diff(self, parts: list) -> bool:
        """Handle /toggle-diff or /diff command."""
        self.app.settings.show_diff = not self.app.settings.show_diff
        self.app.save_settings()
        status = "enabled" if self.app.settings.show_diff else "disabled"
        msg = Text()
        msg.append(f"\nDetailed diff display {status}", style=self.theme_config["success_color"])
        if not self.app.settings.show_diff:
            msg.append(f"\nFile edits will show simplified one-line summaries", style=self.theme_config["dim_color"])
        else:
            msg.append(f"\nFile edits will show full before/after diffs", style=self.theme_config["dim_color"])
        self.app._add_message(msg)
        return True

    def _handle_sessions(self, parts: list) -> bool:
        """Handle /sessions command."""
        from core.history import list_sessions
        sessions = list_sessions()
        msg = Text()
        msg.append("\n📚 Recent Sessions:\n\n", style="bold " + self.theme_config["accent_color"])

        if not sessions:
            msg.append("No sessions found.\n", style=self.theme_config["dim_color"])
        else:
            for session in sessions[:10]:  # Show last 10 sessions
                session_id = session["id"]
                preview = session.get("preview", "")
                msg_count = session.get("message_count", 0)

                if session_id == self.app.agent.history.session_id:
                    msg.append(f"► {session_id}", style="bold " + self.theme_config["success_color"])
                    msg.append(" (current)", style="bold " + self.theme_config["success_color"])
                else:
                    msg.append(f"  {session_id}", style=self.theme_config["tool_color"])

                msg.append(f" - {msg_count} messages", style=self.theme_config["dim_color"])
                if preview:
                    msg.append(f" - {preview}...", style=self.theme_config["text_color"])
                msg.append("\n")

        msg.append(f"\nUse: /load <session_id> to switch sessions\n", style=self.theme_config["dim_color"])
        msg.append(f"Use: /new to start a fresh session\n", style=self.theme_config["dim_color"])
        self.app._add_message(msg)
        return True

    def _handle_new(self, parts: list) -> bool:
        """Handle /new command - start a new session."""
        from core.agent import Agent
        old_session = self.app.agent.history.session_id
        self.app.agent = Agent(
            system_prompt=AGENT_CONFIG["system_prompt"],
            tools=AGENT_CONFIG["tools"],
            model=AGENT_CONFIG["model"],
        )
        msg = Text()
        msg.append(f"\n🆕 Started new session: {self.app.agent.history.session_id}\n", style="bold " + self.theme_config["success_color"])
        msg.append(f"Previous session: {old_session}\n", style=self.theme_config["dim_color"])
        self.app._add_message(msg)
        return True

    def _handle_load(self, parts: list) -> bool:
        """Handle /load <session_id> command."""
        from core.agent import Agent
        if len(parts) == 1:
            msg = Text()
            msg.append(f"\nUsage: /load <session_id>\n", style=self.theme_config["error_color"])
            msg.append(f"Use /sessions to list available sessions\n", style=self.theme_config["dim_color"])
            self.app._add_message(msg)
            return True

        session_id = parts[1]
        try:
            # Try to load the session
            old_session = self.app.agent.history.session_id
            self.app.agent = Agent(
                system_prompt=AGENT_CONFIG["system_prompt"],
                tools=AGENT_CONFIG["tools"],
                model=AGENT_CONFIG["model"],
                session_id=session_id,
            )

            # Load chat history into display
            self.app._load_chat_history()

            msg = Text()
            msg.append(f"\n📂 Loaded session: {session_id}\n", style="bold " + self.theme_config["success_color"])
            msg.append(f"Previous session: {old_session}\n", style=self.theme_config["dim_color"])
            msg.append(f"Loaded {len(self.app.agent.history.messages)} messages\n", style=self.theme_config["dim_color"])
            self.app._add_message(msg)
            return True
        except Exception as e:
            msg = Text()
            msg.append(f"\nFailed to load session: {session_id}\n", style=self.theme_config["error_color"])
            msg.append(f"Error: {str(e)}\n", style=self.theme_config["dim_color"])
            self.app._add_message(msg)
            return True

    def _handle_help(self, parts: list) -> bool:
        """Handle /help command."""
        msg = Text()
        msg.append("\n📖 Prism Help\n\n", style="bold " + self.theme_config["accent_color"])        msg.append("Available Commands:\n", style="bold " + self.theme_config["text_color"])

        for cmd, desc in self.app.get_slash_commands():
            msg.append(f"  {cmd}", style="bold " + self.theme_config["tool_color"])
            msg.append(f" - {desc}\n", style=self.theme_config["text_color"])

        msg.append("\nKeyboard Shortcuts:\n", style="bold " + self.theme_config["text_color"])
        shortcuts = [
            ("Enter", "Send message"),
            ("Ctrl+Enter", "Send multiline message"),
            ("Ctrl+V", "Paste content"),
            ("Ctrl+C", "Clear chat"),
            ("Ctrl+Q", "Quit application"),
            ("Escape", "Stop generation"),
            ("Up/Down", "Navigate autocomplete"),
            ("End", "Scroll to bottom & resume auto-scroll"),
        ]
        for key, desc in shortcuts:
            msg.append(f"  {key}", style="bold " + self.theme_config["tool_color"])
            msg.append(f" - {desc}\n", style=self.theme_config["text_color"])

        msg.append(f"\nCurrent Session: {self.app.agent.history.session_id}\n", style="bold " + self.theme_config["text_color"])
        msg.append(f"Theme: {self.theme_config['name']}\n", style=self.theme_config["dim_color"])
        diff_status = "enabled" if self.app.settings.show_diff else "disabled"
        msg.append(f"Detailed diffs: {diff_status}\n", style=self.theme_config["dim_color"])

        self.app._add_message(msg)
        return True

    def _handle_session(self, parts: list) -> bool:
        """Handle /session command."""
        if len(parts) == 1:
            # Show current session info
            msg = Text()
            msg.append(f"\n📋 Current Session\n\n", style="bold " + self.theme_config["accent_color"])
            msg.append(f"  ID: ", style=self.theme_config["dim_color"])
            msg.append(f"{self.app.agent.history.session_id}\n", style="bold " + self.theme_config["tool_color"])
            msg.append(f"  Messages: ", style=self.theme_config["dim_color"])
            msg.append(f"{len(self.app.agent.history.messages)}\n", style=self.theme_config["text_color"])
            msg.append(f"  Model: ", style=self.theme_config["dim_color"])
            msg.append(f"{self.app.agent.model}\n", style=self.theme_config["text_color"])
            created = self.app.agent.history.metadata.get("created_at", "unknown")
            msg.append(f"  Created: ", style=self.theme_config["dim_color"])
            msg.append(f"{created}\n", style=self.theme_config["text_color"])
            msg.append(f"\nUse /sessions to list all sessions", style=self.theme_config["dim_color"])
            self.app._add_message(msg)
            return True
        elif parts[1].lower() == "new":
            # Redirect to /new
            old_session = self.app.agent.history.session_id
            self.app.agent.new_session()
            self.app.messages = []
            msg = Text()
            msg.append(f"\n🆕 Started new session: {self.app.agent.history.session_id}\n", style="bold " + self.theme_config["success_color"])
            msg.append(f"Previous session: {old_session}\n", style=self.theme_config["dim_color"])
            self.app._add_message(msg)
            return True
        else:
            # Load a specific session by ID
            session_id = parts[1]
            if self.app.agent.load_session(session_id):
                self.app._load_chat_history()
                msg = Text()
                msg.append(f"\n📂 Loaded session: {session_id}\n", style="bold " + self.theme_config["success_color"])
                msg.append(f"Restored {len(self.app.agent.history.messages)} messages\n", style=self.theme_config["dim_color"])
                self.app._add_message(msg)
            else:
                msg = Text()
                msg.append(f"\nSession not found: {session_id}\n", style=self.theme_config["error_color"])
                msg.append(f"Use /sessions to list available sessions\n", style=self.theme_config["dim_color"])
                self.app._add_message(msg)
            return True
