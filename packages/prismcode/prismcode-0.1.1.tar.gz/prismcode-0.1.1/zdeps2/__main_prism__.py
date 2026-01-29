#!/usr/bin/env python3
"""Main entry point for zdeps2 using Prism backend."""
from .api.app_prism import app
from .core.config import get_project_root, get_config_path


def main():
    print()
    print("=" * 55)
    print("  ZDEPS2 - Modular Dependency Viewer (Prism Backend)")
    print("=" * 55)
    print(f"\n  Project Root: {get_project_root()}")
    print(f"  Config File:  {get_config_path()}")
    print(f"\n  Open in browser: http://localhost:5052")
    print("\n  Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5052, debug=False)


if __name__ == "__main__":
    main()
