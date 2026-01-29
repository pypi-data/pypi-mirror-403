"""
Settings management for Prism.
"""
import json
import os

SETTINGS_FILE = "settings.json"


class Settings:
    """Handles loading and saving application settings."""

    def __init__(self):
        self.theme = "github-dark"
        self.show_diff = True
        self.load()

    def load(self) -> None:
        """Load settings from settings.json."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.theme = data.get("theme", "github-dark")
                    self.show_diff = data.get("show_diff", True)
        except Exception:
            pass

    def save(self) -> None:
        """Save settings to settings.json."""
        try:
            data = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)

            data["theme"] = self.theme
            data["show_diff"] = self.show_diff

            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
