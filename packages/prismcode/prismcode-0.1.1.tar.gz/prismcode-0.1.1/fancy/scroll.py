"""Scroll management for chat container."""
from textual.containers import ScrollableContainer
from textual.widgets import Static


class ScrollManager:
    """Manages auto-scroll behavior for the chat container."""

    def __init__(self, app):
        """Initialize with reference to the app for state access."""
        self.app = app
        self.auto_scroll = True
        self.user_scrolled_up = False

    def handle_scroll_event(self, event) -> None:
        """Handle scroll events to detect manual scrolling."""
        # Only process if the scroll container is the target
        if event.control.id != "chat-scroll":
            return

        scroll_container = self.app.query_one("#chat-scroll", ScrollableContainer)

        # Check if we're at the bottom (within a reasonable tolerance)
        max_scroll = scroll_container.max_scroll_y
        current_scroll = scroll_container.scroll_y

        # Store previous state to detect changes
        prev_auto_scroll = self.auto_scroll
        prev_user_scrolled = self.user_scrolled_up

        # Only re-enable auto-scroll if user manually scrolls to the very bottom
        # Use tight tolerance for re-enabling (within 1 line of bottom)
        if max_scroll == 0 or max_scroll - current_scroll <= 1:
            if self.user_scrolled_up:  # Only change if user had previously scrolled up
                self.auto_scroll = True
                self.user_scrolled_up = False
        else:
            # Disable auto-scroll if user scrolls up at all
            # Use smaller threshold to be more sensitive to manual scrolling
            if max_scroll - current_scroll > 2:
                self.auto_scroll = False
                self.user_scrolled_up = True

        # Update status if scroll state changed
        if (prev_auto_scroll != self.auto_scroll or prev_user_scrolled != self.user_scrolled_up):
            if not self.app.processing:
                self.app.query_one("#status", Static).update(self.app._status_text())

    def check_scroll_position(self) -> None:
        """Check if we're at bottom after keyboard scrolling."""
        try:
            scroll_container = self.app.query_one("#chat-scroll", ScrollableContainer)
            max_scroll = scroll_container.max_scroll_y
            current_scroll = scroll_container.scroll_y

            # Store previous state to detect changes
            prev_auto_scroll = self.auto_scroll
            prev_user_scrolled = self.user_scrolled_up

            # Only re-enable auto-scroll if user scrolls to very bottom
            if max_scroll == 0 or max_scroll - current_scroll <= 1:
                if self.user_scrolled_up:  # Only change if user had scrolled up
                    self.auto_scroll = True
                    self.user_scrolled_up = False
            elif max_scroll - current_scroll > 2:
                self.auto_scroll = False
                self.user_scrolled_up = True

            # Update status if scroll state changed
            if (prev_auto_scroll != self.auto_scroll or prev_user_scrolled != self.user_scrolled_up):
                if not self.app.processing:
                    self.app.query_one("#status", Static).update(self.app._status_text())
        except:
            pass

    def force_scroll_to_bottom(self) -> None:
        """Force scroll to bottom and re-enable auto-scroll."""
        self.auto_scroll = True
        self.user_scrolled_up = False
        scroll = self.app.query_one("#chat-scroll", ScrollableContainer)
        scroll.scroll_end(animate=True)

    def scroll_to_bottom_if_auto(self) -> None:
        """Scroll to bottom only if auto-scroll is enabled."""
        if self.auto_scroll:
            scroll = self.app.query_one("#chat-scroll", ScrollableContainer)
            scroll.scroll_end(animate=False)
