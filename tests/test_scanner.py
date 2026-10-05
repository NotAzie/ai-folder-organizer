"""Tests for folder scanner module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from organiser.scanner import (
    FolderScanner,
    FolderStructure,
    FileInfo,
    scan_folder,
    should_exclude,
    PROJECT_INDICATORS,
)


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_creation(self):
        """FileInfo should store all metadata."""
        info = FileInfo(
            rel_path="test/file.txt",
            name="file.txt",
            ext=".txt",
            size_bytes=1024,
            created="2024-01-01T00:00:00",
            modified="2024-01-02T00:00:00",
        )

        assert info.rel_path == "test/file.txt"
        assert info.name == "file.txt"
        assert info.ext == ".txt"
        assert info.size_bytes == 1024

    def test_size_human(self):
        """Size should be formatted human-readably."""
        info = FileInfo(
            rel_path="test.txt",
            name="test.txt",
            ext=".txt",
            size_bytes=500,
            created="2024-01-01",
            modified="2024-01-01",
        )
        assert "500" in info.size_human
        assert "B" in info.size_human


class TestShouldExclude:
    """Tests for should_exclude function."""

    def test_excludes_matching_patterns(self):
        """Should return True for matching patterns."""
        patterns = {'venv', '.git', 'node_modules'}
        assert should_exclude("project/venv/lib", patterns)
        assert should_exclude("project/.git/config", patterns)
        assert should_exclude("project/node_modules/pkg", patterns)

    def test_excludes_case_insensitive(self):
        """Should match case-insensitively."""
        patterns = {'venv'}
        assert should_exclude("project/VENV/lib", patterns)
        assert should_exclude("project/Venv/lib", patterns)

    def test_excludes_windows_paths(self):
        """Should handle Windows backslashes."""
        patterns = {'venv'}
        assert should_exclude("project\\venv\\lib", patterns)

    def test_includes_non_matching(self):
        """Should return False for non-matching paths."""
        patterns = {'venv', '.git'}
        assert not should_exclude("project/src/main.py", patterns)
        assert not should_exclude("project/docs/readme.md", patterns)


class TestFolderScanner:
    """Tests for FolderScanner class."""

    def test_scan_empty_folder(self, tmp_path):
        """Scanning empty folder should return empty structure."""
        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert structure.total_files == 0
        assert len(structure.files) == 0
        assert len(structure.potential_projects) == 0

    def test_scan_single_file(self, tmp_path):
        """Scanning folder with single file."""
        (tmp_path / "test.txt").write_text("content")

        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert structure.total_files == 1
        assert len(structure.files) == 1
        assert structure.files[0].name == "test.txt"

    def test_scan_multiple_files(self, tmp_path):
        """Scanning folder with multiple files."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.py").write_text("content2")
        (tmp_path / "file3.jpg").write_text("content3")

        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert structure.total_files == 3
        assert len(structure.file_counts) == 3
        assert structure.file_counts[".txt"] == 1
        assert structure.file_counts[".py"] == 1
        assert structure.file_counts[".jpg"] == 1

    def test_scan_excludes_patterns(self, tmp_path):
        """Should exclude files in excluded folders."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "venv").mkdir()
        (tmp_path / "venv" / "python.exe").write_text("binary")

        scanner = FolderScanner(tmp_path, exclude_patterns={'venv'})
        structure = scanner.scan()

        assert structure.total_files == 1
        assert structure.files[0].name == "main.py"

    def test_detect_project(self, tmp_path):
        """Should detect project folders."""
        (tmp_path / "myproject").mkdir()
        (tmp_path / "myproject" / "README.md").write_text("# Project")
        (tmp_path / "myproject" / "pyproject.toml").write_text("[project]")

        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert "myproject" in structure.potential_projects

    def test_no_project_without_indicators(self, tmp_path):
        """Should not detect project without indicators."""
        (tmp_path / "misc").mkdir()
        (tmp_path / "misc" / "random.txt").write_text("text")

        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert "misc" not in structure.potential_projects

    def test_scan_subdirectories(self, tmp_path):
        """Should scan subdirectories recursively."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.txt").write_text("nested")

        scanner = FolderScanner(tmp_path)
        structure = scanner.scan()

        assert structure.total_files == 1
        # Path uses OS separator
        assert "subdir" in structure.files[0].rel_path
        assert "nested.txt" in structure.files[0].rel_path

    def test_scan_with_custom_patterns(self, tmp_path):
        """Should use custom exclusion patterns."""
        (tmp_path / "cache").mkdir()
        (tmp_path / "cache" / "temp.dat").write_text("temp")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")

        scanner = FolderScanner(tmp_path, exclude_patterns={'cache'})
        structure = scanner.scan()

        assert structure.total_files == 1
        assert structure.files[0].name == "main.py"


class TestScanFolder:
    """Tests for convenience scan_folder function."""

    def test_scan_folder_function(self, tmp_path):
        """Convenience function should work."""
        (tmp_path / "test.txt").write_text("content")

        structure = scan_folder(tmp_path)

        assert structure.total_files == 1
        assert structure.files[0].name == "test.txt"

    def test_scan_with_exclude_patterns(self, tmp_path):
        """Convenience function should accept exclude patterns."""
        (tmp_path / "venv").mkdir()
        (tmp_path / "venv" / "python.exe").write_text("binary")

        structure = scan_folder(tmp_path, exclude_patterns={'venv'})

        assert structure.total_files == 0
