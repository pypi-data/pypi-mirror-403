"""Agent execution and event handling."""
from rich.text import Text
from rich.console import Group
from rich.markdown import Markdown
from textual.widgets import Static

from .diff import DiffRenderer


class AgentRunner:
    """Handles agent execution and event processing."""

    def __init__(self, app):
        """Initialize with reference to the app for state access."""
        self.app = app
        self.diff_renderer = DiffRenderer(app.theme_config)

    @property
    def theme_config(self):
        return self.app.theme_config

    def update_theme(self, theme_config: dict) -> None:
        """Update theme config after theme change."""
        self.diff_renderer = DiffRenderer(theme_config)

    def run(self, user_input: str) -> None:
        """Run agent with given input. Called from background thread."""
        self.app.current_stream = ""

        def refresh():
            self.app._throttled_refresh()

        def update_status(msg: str):
            self.app.query_one("#status", Static).update(self.app._status_text(msg))

        def commit_stream():
            """Commit current stream to messages."""
            if self.app.current_stream:
                # Render as markdown using Group (same approach as streaming)
                try:
                    markdown_content = Markdown(self.app.current_stream, code_theme=self.theme_config["code_theme"])
                    prefix = Text()
                    prefix.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
                    self.app.messages.append(Group(prefix, markdown_content))
                except:
                    # Fall back to plain text if markdown fails
                    msg = Text()
                    msg.append("Prism: ", style="bold " + self.theme_config["assistant_color"])
                    msg.append(self.app.current_stream, style=self.theme_config["text_color"])
                    self.app.messages.append(msg)

                self.app.current_stream = ""

        def add_tool(name: str, args: dict, result: str):
            """Add tool output to messages."""
            parts = []

            header = Text()
            header.append(f"  {name}", style="bold " + self.theme_config["tool_color"])
            parts.append(header)

            if name == "edit_file" and "old_str" in args and "new_str" in args:
                fp = args.get("file_path", "")

                if self.app.settings.show_diff:
                    # Show minimal unified diff like Claude Code
                    diff_content = self.diff_renderer.create_minimal_diff(args["old_str"], args["new_str"], fp)
                    if diff_content:
                        parts.append(diff_content)
                else:
                    # Show simple one-line summary
                    old_lines = len(args["old_str"].splitlines())
                    new_lines = len(args["new_str"].splitlines())
                    summary_text = Text()
                    summary_text.append(f"    Edited {fp}: ", style=self.theme_config["dim_color"])
                    if old_lines == new_lines:
                        summary_text.append(f"modified {old_lines} line{'s' if old_lines != 1 else ''}", style=self.theme_config["warning_color"])
                    else:
                        summary_text.append(f"changed {old_lines} → {new_lines} lines", style=self.theme_config["warning_color"])
                    parts.append(summary_text)
            else:
                for k, v in args.items():
                    v_str = str(v)[:80] + "..." if len(str(v)) > 80 else str(v)
                    arg_text = Text()
                    arg_text.append(f"    {k}: ", style=self.theme_config["dim_color"])
                    arg_text.append(v_str, style=self.theme_config["warning_color"])
                    parts.append(arg_text)

            if name == "read_file":
                res = Text(f"    Read {len(result.splitlines())} lines", style=self.theme_config["success_color"])
            else:
                r = result[:80] + "..." if len(result) > 80 else result
                res = Text(f"    {r}", style=self.theme_config["success_color"])
            parts.append(res)

            self.app.messages.append(Group(*parts))

        try:
            for event in self.app.agent.stream(user_input):
                if self.app.cancelled:
                    break

                if event.type == "text_delta":
                    self.app.current_stream += event.content
                    self.app.call_from_thread(refresh)

                elif event.type == "text_done":
                    self.app.call_from_thread(commit_stream)
                    self.app.call_from_thread(refresh)

                elif event.type == "tool_start":
                    self.app.call_from_thread(commit_stream)
                    self.app.call_from_thread(update_status, f"running {event.name}...")

                elif event.type == "tool_done":
                    self.app.call_from_thread(add_tool, event.name, event.arguments, event.result)
                    self.app.call_from_thread(refresh)
                    self.app.call_from_thread(update_status, "streaming...")
                    # Refresh focus bar in case focus/unfocus was called
                    if event.name in ("focus", "unfocus"):
                        self.app.call_from_thread(self.app._refresh_focus_bar)

        except Exception as e:
            err = Text(f"Error: {e}", style="bold " + self.theme_config["error_color"])
            self.app.messages.append(err)
            self.app.call_from_thread(refresh)

        finally:
            # Clean up any orphan tool_use blocks from cancellation
            self.app.agent.cleanup_incomplete_tool_calls()
            self.app.processing = False
            self.app.cancelled = False
            self.app.current_stream = ""
            self.app.call_from_thread(update_status, "")
            
            # Check for queued message and send it
            if self.app.queued_message:
                queued = self.app.queued_message
                self.app.queued_message = None
                # Submit the queued message on the main thread
                def send_queued():
                    self.app._submit_input(queued)
                self.app.call_from_thread(send_queued)
            else:
                # Refocus input after processing completes
                def refocus_input():
                    self.app._focus_input()
                self.app.call_from_thread(refocus_input)
