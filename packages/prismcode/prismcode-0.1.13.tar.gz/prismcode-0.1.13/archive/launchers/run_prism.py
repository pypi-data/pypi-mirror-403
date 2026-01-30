#!/usr/bin/env python3
"""Run the zdeps2 web interface with Prism backend."""
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from zdeps2.__main_prism__ import main

if __name__ == "__main__":
    main()
