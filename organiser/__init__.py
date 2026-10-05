"""
AI Folder Organizer - AI-powered directory organization tool.

This package provides tools to scan directories, use LLMs to suggest
 reorganizations, and safely execute file moves with rollback support.
"""

__version__ = "1.0.0"
__author__ = "Mazziula"

from organiser.config import Config, load_config
from organiser.scanner import scan_folder, FolderScanner
from organiser.llm_client import LLMClient, ApiFreeLLMClient
from organiser.proposal import build_prompt, parseproposal, Proposal
from organiser.executor import execute_actions, rollback, ActionExecutor
from organiser.ui.cli import run_cli
from organiser.ui.gui import run_gui

__all__ = [
    "Config",
    "load_config",
    "scan_folder",
    "FolderScanner",
    "LLMClient",
    "ApiFreeLLMClient",
    "build_prompt",
    "parseproposal",
    "Proposal",
    "execute_actions",
    "rollback",
    "ActionExecutor",
    "run_cli",
    "run_gui",
]
