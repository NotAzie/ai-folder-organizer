#!/usr/bin/env python3
"""
AI Folder Organizer - Command Line Interface

This is a backward-compatible entry point that imports from the
refactored organiser package.

Usage:
    python cli.py [options]

For help, run:
    python cli.py --help
"""

from organiser.ui.cli import cli_main

if __name__ == "__main__":
    cli_main()
