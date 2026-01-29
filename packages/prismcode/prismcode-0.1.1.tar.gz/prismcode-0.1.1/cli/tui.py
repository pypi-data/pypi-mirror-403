"""
Prism TUI - curses-based, works everywhere.
NeoVim-inspired aesthetic.
"""
import curses
import threading
import textwrap
from dataclasses import dataclass
from typing import List, Optional
from queue import Queue

from core.agent import Agent
from tools import read_file, create_file, edit_file, rename_file, delete_file, ls


@dataclass
class Message:
    role: str  # user, assistant, tool, system
    content: str


class PrismTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.messages: List[Message] = []
        self.input_buffer = ""
        self.scroll_offset = 0
        self.running = True
        self.busy = False
        self.event_queue: Queue = Queue()

        # Initialize agent
        self.agent = Agent(
            system_prompt="You are a helpful coding assistant. Use tools to read, create, edit, and navigate files. Be concise.",
            tools=[read_file, create_file, edit_file, rename_file, delete_file, ls],
            model="anthropic/claude-opus-4-5",
        )

        # Setup curses
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)

        # Colors
        curses.init_pair(1, 208, -1)   # Orange - primary/user
        curses.init_pair(2, 51, -1)    # Cyan - assistant
        curses.init_pair(3, 243, -1)   # Gray - muted
        curses.init_pair(4, 78, -1)    # Green - success
        curses.init_pair(5, 203, -1)   # Red - error
        curses.init_pair(6, 255, 236)  # Header bg
        curses.init_pair(7, 214, -1)   # Yellow - tool

        self.COLOR_PRIMARY = curses.color_pair(1) | curses.A_BOLD
        self.COLOR_ASSISTANT = curses.color_pair(2) | curses.A_BOLD
        self.COLOR_MUTED = curses.color_pair(3)
        self.COLOR_SUCCESS = curses.color_pair(4)
        self.COLOR_ERROR = curses.color_pair(5)
        self.COLOR_HEADER = curses.color_pair(6)
        self.COLOR_TOOL = curses.color_pair(7)

        # Welcome message
        self.messages.append(Message("system", f"Session: {self.agent.history.session_id}"))

    @property
    def height(self):
        return self.stdscr.getmaxyx()[0]

    @property
    def width(self):
        return self.stdscr.getmaxyx()[1]

    def draw_header(self):
        header = f" ◆ Prism │ {self.agent.model.split('/')[-1]} "
        status = " [busy] " if self.busy else ""
        padding = self.width - len(header) - len(status)
        line = header + " " * max(0, padding) + status
        self.stdscr.attron(self.COLOR_HEADER)
        self.stdscr.addstr(0, 0, line[:self.width].ljust(self.width))
        self.stdscr.attroff(self.COLOR_HEADER)

    def draw_footer(self):
        y = self.height - 1
        hints = " Enter:send │ Ctrl+C:quit │ ↑↓:scroll "
        padding = self.width - len(hints)
        line = hints + " " * max(0, padding)
        self.stdscr.attron(self.COLOR_HEADER)
        self.stdscr.addstr(y, 0, line[:self.width-1])
        self.stdscr.attroff(self.COLOR_HEADER)

    def wrap_message(self, msg: Message) -> List[tuple]:
        """Wrap message content and return lines with attributes."""
        lines = []
        content_width = self.width - 6

        if msg.role == "user":
            prefix = "❯ "
            attr = self.COLOR_PRIMARY
        elif msg.role == "assistant":
            prefix = "◆ "
            attr = self.COLOR_ASSISTANT
        elif msg.role == "tool":
            prefix = "  → "
            attr = self.COLOR_TOOL
        elif msg.role == "tool_result":
            prefix = "  ✓ "
            attr = self.COLOR_SUCCESS
        else:
            prefix = "  "
            attr = self.COLOR_MUTED

        wrapped = textwrap.wrap(msg.content, width=content_width) or [""]
        for i, line in enumerate(wrapped):
            if i == 0:
                lines.append((prefix + line, attr if i == 0 else curses.A_NORMAL))
            else:
                lines.append(("    " + line, curses.A_NORMAL))

        return lines

    def draw_messages(self):
        # Calculate available height for messages
        msg_area_start = 2
        msg_area_end = self.height - 4
        available_lines = msg_area_end - msg_area_start

        # Get all wrapped lines
        all_lines = []
        for msg in self.messages:
            all_lines.extend(self.wrap_message(msg))
            all_lines.append(("", curses.A_NORMAL))  # Blank line

        # Apply scroll
        total_lines = len(all_lines)
        max_scroll = max(0, total_lines - available_lines)
        self.scroll_offset = min(self.scroll_offset, max_scroll)

        # Draw visible lines
        start_idx = max(0, total_lines - available_lines - self.scroll_offset)
        visible = all_lines[start_idx:start_idx + available_lines]

        for i, (line, attr) in enumerate(visible):
            y = msg_area_start + i
            if y < msg_area_end:
                try:
                    self.stdscr.addstr(y, 1, line[:self.width-2].ljust(self.width-2), attr)
                except curses.error:
                    pass

        # Clear remaining lines
        for i in range(len(visible), available_lines):
            y = msg_area_start + i
            if y < msg_area_end:
                try:
                    self.stdscr.addstr(y, 1, " " * (self.width - 2))
                except curses.error:
                    pass

    def draw_input(self):
        y = self.height - 3
        # Draw input box border
        self.stdscr.addstr(y - 1, 0, "─" * self.width, self.COLOR_MUTED)

        # Draw prompt and input
        prompt = "❯ "
        self.stdscr.addstr(y, 1, prompt, self.COLOR_PRIMARY)

        # Show input with cursor
        visible_width = self.width - len(prompt) - 3
        display_text = self.input_buffer[-visible_width:] if len(self.input_buffer) > visible_width else self.input_buffer
        self.stdscr.addstr(y, len(prompt) + 1, display_text.ljust(visible_width))

        # Position cursor
        cursor_x = len(prompt) + 1 + len(display_text)
        self.stdscr.move(y, min(cursor_x, self.width - 2))

    def draw(self):
        self.stdscr.clear()
        self.draw_header()
        self.draw_messages()
        self.draw_input()
        self.draw_footer()
        self.stdscr.refresh()

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role, content))
        self.scroll_offset = 0

    def process_query(self, text: str):
        self.busy = True
        self.draw()

        content = ""
        try:
            for ev in self.agent.stream(text):
                if ev.type == "text_delta":
                    content += ev.content
                    # Update last message if it's assistant
                    if self.messages and self.messages[-1].role == "assistant":
                        self.messages[-1].content = content
                    else:
                        self.add_message("assistant", content)
                    self.event_queue.put("redraw")

                elif ev.type == "tool_start":
                    args = ev.arguments or {}
                    path = args.get("file_path", args.get("path", ""))
                    self.add_message("tool", f"{ev.name} {path}")
                    self.event_queue.put("redraw")

                elif ev.type == "tool_done":
                    short = ev.result[:60].replace('\n', ' ')
                    if len(ev.result) > 60:
                        short += "…"
                    self.add_message("tool_result", short)
                    self.event_queue.put("redraw")

        except Exception as e:
            self.add_message("system", f"Error: {e}")

        self.busy = False
        self.event_queue.put("redraw")

    def handle_input(self, key):
        if key == curses.KEY_RESIZE:
            self.draw()
        elif key == curses.KEY_UP:
            self.scroll_offset += 1
        elif key == curses.KEY_DOWN:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif key == curses.KEY_BACKSPACE or key == 127:
            self.input_buffer = self.input_buffer[:-1]
        elif key == 10 or key == 13:  # Enter
            if self.input_buffer.strip() and not self.busy:
                text = self.input_buffer.strip()
                self.input_buffer = ""
                self.add_message("user", text)
                self.draw()

                # Process in background
                thread = threading.Thread(target=self.process_query, args=(text,))
                thread.daemon = True
                thread.start()
        elif key == 3:  # Ctrl+C
            self.running = False
        elif 32 <= key <= 126:  # Printable
            self.input_buffer += chr(key)

    def run(self):
        self.draw()

        while self.running:
            # Check for events from background thread
            while not self.event_queue.empty():
                event = self.event_queue.get()
                if event == "redraw":
                    self.draw()

            # Non-blocking input check
            self.stdscr.timeout(50)  # 50ms timeout
            try:
                key = self.stdscr.getch()
                if key != -1:
                    self.handle_input(key)
                    self.draw()
            except KeyboardInterrupt:
                self.running = False


def main():
    curses.wrapper(lambda stdscr: PrismTUI(stdscr).run())


if __name__ == "__main__":
    main()
