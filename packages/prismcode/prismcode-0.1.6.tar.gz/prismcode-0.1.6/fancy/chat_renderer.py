"""Chat message rendering utilities."""
from rich.text import Text
from rich.console import Group
from rich.markdown import Markdown
from textual.widgets import Static
from textual.containers import ScrollableContainer


class ChatRenderer:
    """Handles rendering of chat messages and history."""

    def __init__(self, app):
        """Initialize with reference to the app for state access."""
        self.app = app
        self.last_refresh_time = 0

    @property
    def theme_config(self):
        return self.app.theme_config

    def load_chat_history(self) -> None:
        """Load session history into display messages."""
        self.app.messages = []
        for msg in self.app.agent.history.messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                text = Text()
                text.append("You: ", style="bold " + self.theme_config["user_color"])
                text.append(content, style=self.theme_config["text_color"])
                self.app.messages.append(text)
            elif role == "assistant":
                text = Text()
                text.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
                try:
                    markdown_content = Markdown(content, code_theme=self.theme_config["code_theme"])
                    text.append(markdown_content)
                except:
                    text.append(content, style=self.theme_config["text_color"])
                self.app.messages.append(text)
            elif role == "tool":
                tool_name = msg.get("tool_name", "tool")
                text = Text()
                text.append(f"  {tool_name}", style="bold " + self.theme_config["tool_color"])
                self.app.messages.append(text)
        self.refresh()

    def refresh(self) -> None:
        """Re-render the entire chat with current messages + streaming text."""
        content = self.app.query_one("#chat-content", Static)

        # Build display from messages + current stream
        parts = list(self.app.messages)

        if self.app.current_stream:
            # Try to render streaming content as markdown, fall back to plain text
            try:
                markdown_content = Markdown(self.app.current_stream, code_theme=self.theme_config["code_theme"])
                # Use Group to combine the prefix Text with the Markdown content
                prefix = Text()
                prefix.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
                parts.append(Group(prefix, markdown_content))
            except Exception:
                # Fall back to plain text if markdown parsing fails (incomplete syntax, etc.)
                stream_text = Text()
                stream_text.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
                stream_text.append(self.app.current_stream, style=self.theme_config["text_color"])
                parts.append(stream_text)

        if parts:
            content.update(Group(*parts))
        else:
            content.update("")

        # NEVER auto-scroll from refresh - manual scroll position should be preserved

    def throttled_refresh(self) -> None:
        """Throttled refresh for smooth streaming - only refresh every 50ms."""
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self.last_refresh_time > 50:  # 50ms throttle
            self.last_refresh_time = current_time
            self.refresh()  # NEVER auto-scroll during streaming updates
        else:
            # Schedule a delayed refresh if we're throttling
            self.app.set_timer(0.05, self.refresh)

    def create_welcome_message(self) -> Text:
        """Create the welcome message for new sessions."""
        welcome = Text()
        welcome.append("Prism ready!", style="bold " + self.theme_config["success_color"])
        welcome.append(f"  Session: {self.app.agent.history.session_id[:8]}", style=self.theme_config["accent_color"])
        welcome.append(f"  Tools: {', '.join(t.__name__ for t in self.app.agent.tools)}", style=self.theme_config["dim_color"])
        return welcome

    def create_resumed_message(self) -> Text:
        """Create the message for resumed sessions."""
        msg = Text()
        msg.append(f"Resumed session: {self.app.agent.history.session_id}", style="bold " + self.theme_config["success_color"])
        msg.append(f"  {len(self.app.agent.history.messages)} messages", style=self.theme_config["dim_color"])
        return msg

    def create_cleared_message(self) -> Text:
        """Create the message shown after clearing chat."""
        welcome = Text()
        welcome.append("Chat cleared!", style="bold " + self.theme_config["warning_color"])
        welcome.append(f"\nTheme: {self.theme_config['name']}", style=self.theme_config["accent_color"])
        welcome.append(f"\nTools: {', '.join(t.__name__ for t in self.app.agent.tools)}", style=self.theme_config["dim_color"])
        welcome.append(f"\nType /help for available commands", style=self.theme_config["dim_color"])
        return welcome

    def create_user_message(self, text: str) -> Text:
        """Create a formatted user message."""
        msg = Text()
        msg.append("You: ", style="bold " + self.theme_config["user_color"])
        msg.append(text, style=self.theme_config["text_color"])
        return msg

    def create_cancelled_message(self, partial_content: str) -> Text | Group:
        """Create message for cancelled generation."""
        try:
            # Try to render partial markdown with stopped indicator
            content_with_stop = partial_content + "\n\n*[Generation stopped]*"
            msg = Text()
            msg.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
            markdown_content = Markdown(content_with_stop, code_theme=self.theme_config["code_theme"])
            return Group(msg, markdown_content)
        except:
            # Fall back to plain text
            msg = Text()
            msg.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
            msg.append(partial_content, style=self.theme_config["text_color"])
            msg.append(" [stopped]", style="dim italic " + self.theme_config["error_color"])
            return msg

    def create_error_message(self, command: str) -> Text:
        """Create an error message for unknown command."""
        msg = Text()
        msg.append(f"Unknown command: {command}", style=self.theme_config["error_color"])
        msg.append(f"  Type /help for available commands", style=self.theme_config["dim_color"])
        return msg
