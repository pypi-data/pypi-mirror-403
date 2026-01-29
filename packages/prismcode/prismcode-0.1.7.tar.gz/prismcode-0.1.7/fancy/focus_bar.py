"""Focus bar widget - shows focused files with expand/collapse."""
from pathlib import Path
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.message import Message
from textual import on
from rich.text import Text

from core.signella import Signella

_store = Signella()


class FocusBar(Widget):
    """Expandable bar showing focused files."""
    
    expanded = reactive(False)
    
    class FileUnfocused(Message):
        """Message sent when a file is unfocused."""
        def __init__(self, file_path: str):
            self.file_path = file_path
            super().__init__()
    
    def __init__(self, theme: dict, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.theme = theme
        self.session_id = session_id
    
    def _get_focused_files(self) -> list:
        """Get focused files from Signella."""
        files = _store.get('focus', self.session_id, 'files', default=[])
        return list(files) if files else []
    
    def compose(self):
        yield Static("", id="focus-content")
    
    def on_mount(self):
        self.refresh_display()
    
    def refresh_display(self):
        """Update the focus bar display."""
        focused = self._get_focused_files()
        content = self.query_one("#focus-content", Static)
        
        if not focused:
            content.update("")
            self.add_class("hidden")
            return
        
        self.remove_class("hidden")
        cwd = Path.cwd()
        
        text = Text()
        accent = self.theme.get("accent_color", "cyan")
        dim = self.theme.get("dim_color", "dim")
        
        if self.expanded:
            # Expanded view: show all files with [x] to unfocus
            text.append("📌 ", style=accent)
            for i, abs_path in enumerate(sorted(focused)):
                p = Path(abs_path)
                rel_path = str(p.relative_to(cwd) if p.is_relative_to(cwd) else p)
                
                if i > 0:
                    text.append("  ", style=dim)
                
                text.append(rel_path, style="bold")
                text.append(f" [x:{i}]", style=dim)
            
            text.append("  [collapse]", style=dim)
        else:
            # Collapsed view: just show count
            count = len(focused)
            text.append(f"📌 {count} file{'s' if count != 1 else ''} focused", style=accent)
            text.append("  [expand]", style=dim)
        
        content.update(text)
    
    def on_click(self, event):
        """Handle clicks to expand/collapse or unfocus files."""
        # Toggle expanded state on any click for now
        # TODO: Parse click position to handle [x] buttons
        self.expanded = not self.expanded
    
    def watch_expanded(self, expanded: bool):
        """React to expanded state changes."""
        self.refresh_display()
    
    def update_session(self, session_id: str):
        """Update the session ID and refresh."""
        self.session_id = session_id
        self.refresh_display()
    
    def update_theme(self, theme: dict):
        """Update theme and refresh."""
        self.theme = theme
        self.refresh_display()
