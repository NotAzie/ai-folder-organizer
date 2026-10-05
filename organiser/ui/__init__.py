"""
UI modules for AI Folder Organizer.

Provides both CLI and GUI interfaces for interacting with the organizer.
"""

from organiser.ui.cli import run_cli, cli_main
from organiser.ui.gui import run_gui, gui_main

__all__ = ["run_cli", "cli_main", "run_gui", "gui_main"]
