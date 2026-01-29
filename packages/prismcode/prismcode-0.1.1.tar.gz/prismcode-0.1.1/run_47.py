
#!/usr/bin/env python3
"""
Fancy Textual TUI for Prism agent.
Optimized for performance, visual clarity, and ease of use.
"""
import time
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Header, Footer, TextArea, Markdown
from textual.binding import Binding
from textual import work, on
from rich.text import Text

# External dependencies
from core.agent import Agent
from core.history import list_sessions
from themes import THEMES
from settings import Settings
from config import LANG_MAP, AGENT_CONFIG, SLASH_COMMANDS

def generate_css(theme: dict) -> str:
    """Generate theme-compliant CSS from theme configuration."""
    return f"""
    Screen {{
        background: {theme['screen_bg']};
    }}

    /* Main Layout */
    #main {{
        width: 100%;
        height: 100%;
        layout: vertical;
    }}

    /* Chat Area */
    #chat-scroll {{
        height: 1fr;
        width: 100%;
        border: none;
        background: {theme['screen_bg']};
        scrollbar-size: 1 1;
        scrollbar-color: {theme['scrollbar_color']};
        scrollbar-background: {theme['scrollbar_bg']};
        overflow-y: auto;
    }}

    #chat-history {{
        width: 100%;
        padding: 1 2;
    }}

    /* Message Styling */
    .message {{
        margin: 0 0 1 0;
        width: 100%;
    }}
    
    .user-msg {{
        text-align: right;
    }}

    .agent-name {{
        color: {theme['assistant_color']};
        text-style: bold;
        margin-bottom: 1;
    }}

    /* Active Stream Widget */
    #active-stream {{
        margin-top: 1;
        padding: 0 2;
    }}

    /* Input Area */
    #input-container {{
        width: 100%;
        height: auto;
        padding: 1 2;
        background: {theme['screen_bg']};
        border-top: solid {theme['chat_border']};
    }}

    #prompt {{
        width: 2;
        content-align: right middle;
        color: {theme['user_color']};
        text-style: bold;
    }}

    #input {{
        width: 1fr;
        min-height: 3;
        max-height: 10;
        border: solid {theme['chat_border']};
        background: {theme['input_bg']};
        color: {theme['text_color']};
        padding: 0 1;
    }}

    #input:focus {{
        border: double {theme['accent_color']};
    }}

    /* Autocomplete */
    #autocomplete {{
        width: 60%;
        max-height: 15;
        background: {theme['input_bg']};
        border: round {theme['accent_color']};
        padding: 0;
        display: none;
        margin-bottom: 1;
    }}

    #autocomplete.show {{
        display: block;
    }}

    .ac-item {{
        padding: 0 1;
        height: 1;
    }}
    .ac-item.selected {{
        background: {theme['accent_color']};
        color: {theme['screen_bg']};
        text-style: bold;
    }}

    /* Footer & Header Overrides */
    Header {{
        background: {theme['header_bg']};
        color: {theme['accent_color']};
        text-align: center;
    }}
    
    Footer {{
        background: {theme['footer_bg']};
    }}
    """


class PrismApp(App):
    TITLE = "Prism"
    BINDINGS = [
        Binding("ctrl+c", "clear", "Clear", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("escape", "cancel", "Stop Generation", show=True, priority=True),
        Binding("ctrl+v", "paste", "Paste", show=False),
    ]

    def __init__(self, theme_name: str = "github-dark", session_id: str = None):
        super().__init__()

        self.settings = Settings()
        
        # Theme Setup
        self.theme_name = self.settings.theme if self.settings.theme in THEMES else theme_name
        self.theme_config = THEMES[self.theme_name]
        self.CSS = generate_css(self.theme_config)

        # Agent Setup
        self.agent = Agent(
            system_prompt=AGENT_CONFIG["system_prompt"],
            tools=AGENT_CONFIG["tools"],
            model=AGENT_CONFIG["model"],
            session_id=session_id,
        )
        
        # State
        self.processing = False
        self.cancelled = False
        self.current_stream_text = ""
        
        # UI State
        self.auto_scroll = True
        self.user_scrolled_up = False
        self.last_refresh_time = 0
        
        # Autocomplete State
        self.show_autocomplete = False
        self.autocomplete_options = []
        self.autocomplete_selected = 0

    # --- UI Composition ---

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main"):
            # Chat History (Static Messages)
            with ScrollableContainer(id="chat-scroll"):
                with Vertical(id="chat-history"):
                    pass
            
            # Active Stream (The message currently being typed)
            yield Static("", id="active-stream")
            
            # Autocomplete Overlay
            yield Vertical(id="autocomplete")
            
            # Input Area
            with Horizontal(id="input-container"):
                yield Static("➜ ", id="prompt")
                yield TextArea(
                    "",
                    id="input",
                    show_line_numbers=False,
                    soft_wrap=True,
                )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input").focus()
        
        # Restore history or show welcome
        if self.agent.history.messages:
            self._load_chat_history()
            self._add_system_message(f"Resumed session: {self.agent.history.session_id[:8]}")
        else:
            self._add_system_message(f"Prism Ready! Session: {self.agent.history.session_id[:8]}")
            self._add_system_message(f"Type /help for commands.")

    # --- Input Handling ---

    @on(TextArea.Changed, "#input")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        """Handle input changes for autocomplete."""
        text = event.text_area.text
        # Check last line for slash command
        lines = text.split('\n')
        if lines and lines[-1].lstrip().startswith('/'):
            self.update_autocomplete(lines[-1].lstrip())
        else:
            self.show_autocomplete = False
        self._update_autocomplete_display()

    def on_key(self, event) -> None:
        """Unified key handler for input area."""
        # Only handle if input is focused
        if not self.query_one("#input").has_focus:
            return

        key = event.key

        # 1. Autocomplete Navigation
        if self.show_autocomplete:
            if key == "up":
                self.autocomplete_selected = max(0, self.autocomplete_selected - 1)
                self._update_autocomplete_display()
                event.prevent_default()
                return
            elif key == "down":
                self.autocomplete_selected = min(len(self.autocomplete_options) - 1, self.autocomplete_selected + 1)
                self._update_autocomplete_display()
                event.prevent_default()
                return
            elif key == "tab":
                self._apply_autocomplete()
                event.prevent_default()
                return
            elif key == "escape":
                self.show_autocomplete = False
                self._update_autocomplete_display()
                event.prevent_default()
                return

        # 2. Submission Logic
        if key == "enter":
            # Standard Enter -> Submit
            text = self.query_one("#input").text.strip()
            if text:
                self._submit_input(text)
            event.prevent_default()
            return

    def _apply_autocomplete(self):
        """Replace text with selected autocomplete option."""
        if not self.autocomplete_options:
            return
        
        selected_cmd = self.autocomplete_options[self.autocomplete_selected][0]
        ta = self.query_one("#input")
        
        # Replace the last line
        lines = ta.text.split('\n')
        if lines:
            # Simplified: just replace last line content
            lines[-1] = selected_cmd + " "
            ta.text = '\n'.join(lines)
            ta.move_cursor((ta.cursor_location[0], len(selected_cmd) + 1))
        
        self.show_autocomplete = False
        self._update_autocomplete_display()

    # --- Actions ---

    def action_clear(self) -> None:
        self.query_one("#chat-history", Vertical).remove_children()
        self.query_one("#active-stream", Static).update("")
        self._add_system_message("Chat cleared.")

    def action_paste(self) -> None:
        # Textual handles paste, we just ensure focus
        self.query_one("#input").focus()

    def action_cancel(self) -> None:
        if self.processing:
            self.cancelled = True
            self._add_system_message("Generation stopped by user.", style="bold yellow")

    # --- Core Logic ---

    def _submit_input(self, text: str) -> None:
        if self.processing:
            return

        # Clear input
        input_widget = self.query_one("#input", TextArea)
        input_widget.text = ""
        self.show_autocomplete = False
        self._update_autocomplete_display()

        # Handle Commands
        if text.startswith("/"):
            if self.handle_slash_command(text):
                return
            else:
                self._add_system_message(f"Unknown command: {text}", style="bold red")
                return

        # Add User Message (Render immediately as a widget)
        self._add_user_message(text)
        
        # Reset Stream state
        self.current_stream_text = ""
        self.processing = True
        self.cancelled = False
        self.auto_scroll = True # Force scroll to bottom on new msg

        # Start Agent
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, user_input: str) -> None:
        """Background worker for agent streaming."""
        
        def update_stream():
            # Only update the text of the active stream widget
            stream_widget = self.query_one("#active-stream", Static)
            
            display_text = Text()
            display_text.append("Prism: ", style=self.theme_config["assistant_color"])
            display_text.append(self.current_stream_text)
            
            stream_widget.update(display_text)
            
            if self.auto_scroll:
                self.call_later(self._scroll_to_end)

        def commit_stream():
            # Convert the plain text stream into a permanent Markdown widget
            history = self.query_one("#chat-history", Vertical)
            stream_widget = self.query_one("#active-stream", Static)
            
            # Create a permanent message widget
            msg_widget = Markdown(self.current_stream_text, id=f"msg-{int(time.time())}")
            msg_widget.add_class("message")
            
            # Mount it to history
            history.mount(msg_widget)
            
            # Clear the stream widget
            stream_widget.update("")
            
            # Scroll
            if self.auto_scroll:
                self.call_later(self._scroll_to_end)

        try:
            for event in self.agent.stream(user_input):
                if self.cancelled:
                    break

                if event.type == "text_delta":
                    self.current_stream_text += event.content
                    # Throttle UI updates slightly
                    self.call_from_thread(update_stream)

                elif event.type == "text_done":
                    self.call_from_thread(commit_stream)
                    self.current_stream_text = ""

                elif event.type == "tool_start":
                    self.call_from_thread(commit_stream) # Finish previous text
                    self.call_from_thread(self._add_tool_start, event.name)

                elif event.type == "tool_done":
                    self.call_from_thread(self._add_tool_done, event.name, event.arguments, event.result)

        except Exception as e:
            self.call_from_thread(self._add_system_message, f"Error: {e}", "bold red")
        finally:
            self.processing = False
            self.cancelled = False
            self.current_stream_text = ""
            # Ensure we clear the stream widget if cancelled mid-stream
            self.call_from_thread(lambda: self.query_one("#active-stream", Static).update(""))

    # --- Helpers & Rendering ---

    def _add_user_message(self, text: str):
        history = self.query_one("#chat-history", Vertical)
        msg = Text()
        msg.append("You: ", style="bold " + self.theme_config["user_color"])
        msg.append(text)
        history.mount(Static(msg, classes="message"))
        self._scroll_to_end()

    def _add_system_message(self, text: str, style: str = "dim"):
        history = self.query_one("#chat-history", Vertical)
        msg = Text(text, style=style)
        history.mount(Static(msg, classes="message"))
        self._scroll_to_end()

    def _add_tool_start(self, name: str):
        history = self.query_one("#chat-history", Vertical)
        msg = Text()
        msg.append(f"  ▶ {name} ", style="bold " + self.theme_config["tool_color"])
        history.mount(Static(msg, classes="message"))
        self._scroll_to_end()

    def _add_tool_done(self, name: str, args: dict, result: str):
        # Simplified display
        pass 

    def _load_chat_history(self):
        history = self.query_one("#chat-history", Vertical)
        history.remove_children()
        
        for msg in self.agent.history.messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "user":
                text = Text()
                text.append("You: ", style="bold " + self.theme_config["user_color"])
                text.append(content)
                history.mount(Static(text, classes="message"))
                
            elif role == "assistant":
                # Render as full Markdown for history
                md = Markdown(content)
                # Prepend name
                header = Text("Prism: ", style="bold " + self.theme_config["assistant_color"])
                
                # Container to hold both
                container = Vertical()
                container.mount(Static(header))
                container.mount(md)
                container.add_class("message")
                history.mount(container)

    def _scroll_to_end(self):
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.scroll_end(animate=False)

    def on_scroll_view_scroll(self, event) -> None:
        """Detect if user manually scrolled up to stop auto-scroll."""
        if event.control.id != "chat-scroll":
            return
            
        scroll = event.control
        at_bottom = scroll.is_vertical_scrolled_to_end
        
        if not at_bottom:
            # If user scrolled up significantly
            if self.auto_scroll:
                self.auto_scroll = False
                self.user_scrolled_up = True
        else:
            # If they scrolled back to bottom, re-enable
            if not self.auto_scroll:
                self.auto_scroll = True
                self.user_scrolled_up = False

    # --- Autocomplete Logic ---

    def get_slash_commands(self):
        return SLASH_COMMANDS + [
            ("/sessions", "List recent sessions"),
            ("/new", "Start new session"),
            ("/theme <name>", "Switch theme"),
            ("/clear", "Clear screen"),
        ]

    def update_autocomplete(self, text: str):
        if not text.startswith("/"):
            self.show_autocomplete = False
            return

        commands = self.get_slash_commands()
        matches = [cmd for cmd, desc in commands if cmd.startswith(text)]
        
        if matches:
            self.autocomplete_options = [(cmd, desc) for cmd, desc in commands if cmd.startswith(text)]
            self.show_autocomplete = True
            self.autocomplete_selected = 0
        else:
            self.show_autocomplete = False

    def _update_autocomplete_display(self):
        ac_container = self.query_one("#autocomplete", Vertical)
        ac_container.remove_children()
        
        if not self.show_autocomplete or not self.autocomplete_options:
            ac_container.remove_class("show")
            return

        ac_container.add_class("show")
        
        for i, (cmd, desc) in enumerate(self.autocomplete_options):
            style = "selected" if i == self.autocomplete_selected else ""
            item = Text(f"{cmd} - {desc}")
            # Highlight selection logic
            if i == self.autocomplete_selected:
                item.stylize("bold white on " + self.theme_config['accent_color'])
            else:
                item.stylize(self.theme_config['text_color'])
            
            ac_container.mount(Static(item, classes=f"ac-item {style}"))

    # --- Slash Commands ---
    
    def handle_slash_command(self, command: str) -> bool:
        parts = command[1:].split()
        if not parts: return False
        cmd = parts[0].lower()
        
        if cmd == "new":
            self.agent.new_session()
            self.query_one("#chat-history", Vertical).remove_children()
            self._add_system_message("Started new session.")
            return True
            
        elif cmd == "clear":
            self.action_clear()
            return True

        elif cmd == "theme":
            if len(parts) == 2:
                new_theme = parts[1]
                if new_theme in THEMES:
                    self.set_theme(new_theme)
                    self._add_system_message(f"Theme changed to {new_theme}")
                else:
                    self._add_system_message(f"Theme not found. Available: {', '.join(THEMES.keys())}")
            return True

        return False

    def set_theme(self, theme_name: str):
        if theme_name in THEMES:
            self.theme_name = theme_name
            self.theme_config = THEMES[theme_name]
            self.CSS = generate_css(self.theme_config)
            self.refresh_css()

def main():
    import sys
    app = PrismApp()
    app.run()

if __name__ == "__main__":
    main()