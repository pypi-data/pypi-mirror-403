"""Flask application using Prism backend.

This is a drop-in replacement for app.py that uses the new Prism architecture.
"""
from pathlib import Path
from flask import Flask
from .routes_prism import api

# Get the zdeps2 package directory
PACKAGE_DIR = Path(__file__).parent.parent


def create_app():
    """Create Flask application with Prism backend."""
    app = Flask(
        __name__,
        template_folder=str(PACKAGE_DIR / "templates"),
        static_folder=str(PACKAGE_DIR / "static"),
    )
    app.register_blueprint(api)
    return app


app = create_app()
