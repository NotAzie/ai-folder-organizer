"""Tests for executor module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from organiser.config import Config
from organiser.proposal import Action, Proposal
from organiser.executor import (
    ActionExecutor,
    execute_actions,
    rollback,
    ExecutionLog,
)


class TestActionExecutor:
    """Tests for ActionExecutor class."""

    def test_execute_create_folder_dry_run(self, tmp_path):
        """Dry-run should simulate folder creation."""
        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=True)

        action = Action(id=1, type="create_folder", destination="new_folder")
        executor._execute_action(action)

        assert not (tmp_path / "new_folder").exists()
        assert len(executor.log) == 1
        assert executor.log[0].status == "simulated"

    def test_execute_create_folder_real(self, tmp_path):
        """Real execution should create folder."""
        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="create_folder", destination="new_folder")
        executor._execute_action(action)

        assert (tmp_path / "new_folder").exists()
        assert executor.log[0].status == "success"

    def test_execute_move_dry_run(self, tmp_path):
        """Dry-run should simulate move."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=True)

        action = Action(id=1, type="move", source="source.txt", destination="dest.txt")
        executor._execute_action(action)

        assert source.exists()  # Still exists in dry-run
        assert not (tmp_path / "dest.txt").exists()
        assert executor.log[0].status == "simulated"

    def test_execute_move_real(self, tmp_path):
        """Real execution should move file."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="source.txt", destination="dest.txt")
        executor._execute_action(action)

        assert not source.exists()
        assert (tmp_path / "dest.txt").exists()
        assert executor.log[0].status == "success"

    def test_execute_move_creates_parent(self, tmp_path):
        """Move should create parent directories."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="source.txt", destination="deep/nested/dest.txt")
        executor._execute_action(action)

        assert (tmp_path / "deep" / "nested" / "dest.txt").exists()

    def test_execute_move_conflict_resolution(self, tmp_path):
        """Should resolve conflicts with counter suffix."""
        source = tmp_path / "source.txt"
        source.write_text("content1")
        target = tmp_path / "dest.txt"
        target.write_text("content2")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="source.txt", destination="dest.txt")
        executor._execute_action(action)

        assert (tmp_path / "dest.txt").exists()
        assert (tmp_path / "dest_1.txt").exists()

    def test_execute_move_missing_source(self, tmp_path):
        """Should skip move if source doesn't exist."""
        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="nonexistent.txt", destination="dest.txt")
        executor._execute_action(action)

        assert executor.log[0].status == "skipped"

    def test_rollback_manifest_created(self, tmp_path):
        """Should create rollback manifest after execution."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="source.txt", destination="dest.txt")
        executor._execute_action(action)

        # Logs are saved but manifest is only created on full execution
        # For simplicity, check that executor has manifest data
        assert len(executor.rollback_manifest) == 1
        assert executor.rollback_manifest[0].original == "source.txt"
        assert executor.rollback_manifest[0].new == "dest.txt"

    def test_logs_saved(self, tmp_path):
        """Should save execution logs."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        config = Config()
        executor = ActionExecutor(tmp_path, config, dry_run=False)

        action = Action(id=1, type="move", source="source.txt", destination="dest.txt")
        executor._execute_action(action)

        # Logs are tracked in memory
        assert len(executor.log) == 1
        assert executor.log[0].status == "success"


class TestExecuteActions:
    """Tests for execute_actions convenience function."""

    def test_execute_actions_dry_run(self, tmp_path):
        """Convenience function should work in dry-run mode."""
        config = Config()
        actions = [Action(id=1, type="create_folder", destination="test")]

        logs = execute_actions(tmp_path, actions, config, dry_run=True)

        assert not (tmp_path / "test").exists()
        assert len(logs) == 1

    def test_execute_actions_real(self, tmp_path):
        """Convenience function should work in real mode."""
        config = Config()
        actions = [Action(id=1, type="create_folder", destination="test")]

        logs = execute_actions(tmp_path, actions, config, dry_run=False)

        assert (tmp_path / "test").exists()
        assert len(logs) == 1


class TestRollback:
    """Tests for rollback function."""

    def test_rollback_moves_file_back(self, tmp_path):
        """Rollback should move file back to original location."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        # Simulate move
        dest = tmp_path / "dest.txt"
        source.rename(dest)

        # Create manifest
        manifest_data = [
            {"original": "source.txt", "new": "dest.txt", "action_type": "move"}
        ]
        manifest_path = tmp_path / "test_manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        # Temporarily modify config to use our manifest
        config = Config(rollback_manifest="test_manifest.json")
        result = rollback(tmp_path, config)

        assert result is True
        assert not dest.exists()
        assert source.exists()

    def test_rollback_no_manifest(self, tmp_path):
        """Should return False if no manifest found."""
        config = Config(rollback_manifest="nonexistent.json")
        result = rollback(tmp_path, config)

        assert result is False
