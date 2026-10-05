"""
Action execution and rollback module.

Executes file operations (move, rename, create folder) with safety features:
- Dry-run mode (simulation without actual changes)
- Rollback capability via manifest
- Conflict resolution (duplicate file names)
- Comprehensive logging
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from tqdm import tqdm

from organiser.config import Config
from organiser.proposal import Action, Proposal


@dataclass
class ExecutionLog:
    """Log entry for a single executed action."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    action_type: str = ""
    source: str = ""
    destination: str = ""
    status: str = ""  # "success", "skipped", "error"
    error_message: str = ""


@dataclass
class RollbackEntry:
    """Entry in rollback manifest for reverting an action."""

    original: str  # Original path (relative to root)
    new: str  # New path after operation (relative to root)
    action_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ActionExecutor:
    """
    Executes organization actions with safety features.

    Features:
    - Dry-run mode for preview
    - Automatic rollback manifest generation
    - Conflict resolution for duplicate filenames
    - Comprehensive logging
    """

    def __init__(self, root: Path, config: Config, dry_run: bool = True):
        self.root = root.resolve()
        self.config = config
        self.dry_run = dry_run
        self.log: list[ExecutionLog] = []
        self.rollback_manifest: list[RollbackEntry] = []

    def execute_proposal(self, proposal: Proposal) -> list[ExecutionLog]:
        """
        Execute all actions in a proposal.

        Args:
            proposal: Proposal containing actions to execute.

        Returns:
            List of execution logs.
        """
        for action in tqdm(
            proposal.actions,
            desc="Executing" if not self.dry_run else "Simulating",
        ):
            self._execute_action(action)

        self._save_logs()
        return self.log

    def _execute_action(self, action: Action) -> None:
        """Execute a single action."""
        try:
            if action.type == "create_folder":
                self._create_folder(action)
            elif action.type in ("move", "rename"):
                self._move_or_rename(action)
            else:
                self.log.append(ExecutionLog(
                    action_type=action.type,
                    status="error",
                    error_message=f"Unknown action type: {action.type}",
                ))
        except Exception as e:
            self.log.append(ExecutionLog(
                action_type=action.type,
                source=action.source,
                destination=action.destination or action.new_name,
                status="error",
                error_message=str(e),
            ))

    def _create_folder(self, action: Action) -> None:
        """Create a folder."""
        target = self.root / action.destination
        if self.dry_run:
            self.log.append(ExecutionLog(
                action_type="create_folder",
                destination=str(target.relative_to(self.root)),
                status="simulated",
            ))
            return

        target.mkdir(parents=True, exist_ok=True)
        self.log.append(ExecutionLog(
            action_type="create_folder",
            destination=str(target.relative_to(self.root)),
            status="success",
        ))

    def _move_or_rename(self, action: Action) -> None:
        """Move or rename a file/folder."""
        source = self.root / action.source
        if not source.exists():
            self.log.append(ExecutionLog(
                action_type=action.type,
                source=action.source,
                status="skipped",
                error_message="Source does not exist",
            ))
            return

        # Determine target path
        if action.destination:
            target = self.root / action.destination
        else:
            parent = source.parent
            new_name = action.new_name or source.name
            target = parent / new_name

        # Handle conflicts
        if not self.dry_run and target.exists() and target != source:
            target = self._resolve_conflict(target)

        if self.dry_run:
            self.log.append(ExecutionLog(
                action_type=action.type,
                source=action.source,
                destination=str(target.relative_to(self.root)),
                status="simulated",
            ))
            return

        # Execute move
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))

        # Record for rollback
        self.rollback_manifest.append(RollbackEntry(
            original=action.source,
            new=str(target.relative_to(self.root)),
            action_type=action.type,
        ))

        self.log.append(ExecutionLog(
            action_type=action.type,
            source=action.source,
            destination=str(target.relative_to(self.root)),
            status="success",
        ))

    def _resolve_conflict(self, target: Path) -> Path:
        """
        Resolve filename conflict by adding counter suffix.

        Args:
            target: Target path that already exists.

        Returns:
            New unique path.
        """
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while target.exists():
            target = target.with_name(f"{stem}_{counter}{suffix}")
            counter += 1
        return target

    def _save_logs(self) -> None:
        """Save execution log and rollback manifest."""
        log_path = self.root / self.config.log_file
        manifest_path = self.root / self.config.rollback_manifest

        # Save log
        log_data = [
            {
                "timestamp": entry.timestamp,
                "type": entry.action_type,
                "source": entry.source,
                "destination": entry.destination,
                "status": entry.status,
                "error": entry.error_message,
            }
            for entry in self.log
        ]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

        # Save rollback manifest
        manifest_data = [
            {
                "original": entry.original,
                "new": entry.new,
                "action_type": entry.action_type,
                "timestamp": entry.timestamp,
            }
            for entry in self.rollback_manifest
        ]
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)


def execute_actions(
    root: Path,
    actions: list[Action],
    config: Config,
    dry_run: bool = True,
) -> list[ExecutionLog]:
    """
    Convenience function to execute actions.

    Args:
        root: Root directory.
        actions: List of actions to execute.
        config: Configuration.
        dry_run: If True, simulate without making changes.

    Returns:
        List of execution logs.
    """
    proposal = Proposal(actions=actions)
    executor = ActionExecutor(root, config, dry_run)
    return executor.execute_proposal(proposal)


def rollback(root: Path, config: Config) -> bool:
    """
    Rollback operations using the manifest.

    Args:
        root: Root directory.
        config: Configuration.

    Returns:
        True if rollback completed, False if no manifest found.
    """
    manifest_path = root / config.rollback_manifest
    if not manifest_path.exists():
        print("No rollback manifest found.")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("Rolling back...")
    for entry in reversed(manifest):
        original = root / entry["original"]
        new = root / entry["new"]
        if new.exists():
            # Create parent directory if needed
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(new), str(original))

    print("Rollback complete.")
    return True
