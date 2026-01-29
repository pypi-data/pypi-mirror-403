"""Main entry point for the Eternity application."""

import uvicorn

from .main import app  # noqa: F401


def start():
    """Entry point for the application script"""
    uvicorn.run("eternity.main:app",
        host="0.0.0.0", port=8000, reload=True)  # noqa: S104

if __name__ == "__main__":
    start()
