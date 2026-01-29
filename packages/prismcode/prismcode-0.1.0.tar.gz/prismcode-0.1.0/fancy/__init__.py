"""Fancy Textual TUI for Prism agent."""
from .app import PrismAppfrom .session_picker import show_session_picker
from .command_input import CommandInputBar
from .command_menu import CommandMenu
from .focus_bar import FocusBar

__all__ = ["PrismApp", "show_session_picker", "CommandInputBar", "CommandMenu", "FocusBar", "main"]

def main():
    """Main entry point for the TUI."""
    import sys

    session_id = None

    # Check for --new flag to skip session picker
    if "--new" not in sys.argv:
        session_id = show_session_picker()

    app = PrismApp(session_id=session_id)    app.run(mouse=False)  # Disable mouse capture to allow terminal text selection
