"""
Folder scanning and inventory module.

Scans directories to build a comprehensive file inventory,
detect projects, and identify loose files.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FileInfo:
    """Information about a single file."""

    rel_path: str
    name: str
    ext: str
    size_bytes: int
    created: str
    modified: str

    @property
    def size_human(self) -> str:
        """Human-readable file size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size_bytes < 1024:
                return f"{self.size_bytes:.1f} {unit}"
            self.size_bytes /= 1024
        return f"{self.size_bytes:.1f} PB"


@dataclass
class FolderStructure:
    """Complete folder structure inventory."""

    root_path: Path
    files: list[FileInfo] = field(default_factory=list)
    file_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    potential_projects: list[str] = field(default_factory=list)
    loose_files: list[FileInfo] = field(default_factory=list)
    top_level_summary: dict[str, Any] = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        """Total number of files scanned."""
        return len(self.files)


# Project detection indicators
PROJECT_INDICATORS = {
    'requirements.txt', 'package.json', 'pom.xml', 'setup.py',
    'Cargo.toml', 'pyproject.toml', '.git', 'src', 'lib', 'tests', 'docs',
    'Cargo.lock', 'yarn.lock', 'composer.json', 'Gemfile', 'Makefile',
    'CMakeLists.txt', 'build.gradle', 'gradlew', 'index.js', 'main.py',
}


def should_exclude(path_str: str, exclude_patterns: set[str]) -> bool:
    """
    Check if a path should be excluded from scanning.

    Args:
        path_str: Relative path string to check.
        exclude_patterns: Set of patterns to exclude.

    Returns:
        True if the path should be excluded, False otherwise.
    """
    normalized = path_str.lower().replace('\\', '/')
    for pattern in exclude_patterns:
        if pattern in normalized:
            return True
    return False


class FolderScanner:
    """
    Scans a folder tree and builds a comprehensive inventory.

    Attributes:
        root: Root directory to scan.
        exclude_patterns: Patterns to exclude from scanning.
    """

    def __init__(self, root: Path, exclude_patterns: set[str] | None = None):
        self.root = root.resolve()
        self.exclude_patterns = exclude_patterns or set()
        self.structure = FolderStructure(root_path=self.root)

    def scan(self) -> FolderStructure:
        """
        Perform the folder scan.

        Returns:
            FolderStructure with complete inventory.
        """
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = Path(dirpath).relative_to(self.root)
            rel_str = str(rel_dir) if rel_dir != Path('.') else ""

            # Skip excluded folders
            if should_exclude(rel_str, self.exclude_patterns):
                dirnames[:] = []  # Prevent recursion
                continue

            # Detect projects
            is_project = self._detect_project(dirpath, dirnames, filenames)
            if is_project and rel_str:
                self.structure.potential_projects.append(rel_str)

            # Process files
            for f in filenames:
                if f.startswith('.') and f != '.git':
                    continue

                full_path = Path(dirpath) / f
                rel_path = rel_dir / f if rel_dir != Path('.') else Path(f)

                try:
                    stat = full_path.stat()
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue

                ext = full_path.suffix.lower()
                self.structure.file_counts[ext] += 1

                file_info = FileInfo(
                    rel_path=str(rel_path),
                    name=f,
                    ext=ext,
                    size_bytes=stat.st_size,
                    created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                )
                self.structure.files.append(file_info)

                if not rel_dir.parts:
                    self.structure.loose_files.append(file_info)

            # Top-level summary
            if len(rel_dir.parts) <= 1:
                key = rel_str or "ROOT"
                self.structure.top_level_summary[key] = {
                    "file_count": len(filenames),
                    "subfolders": len(dirnames),
                    "is_project": is_project,
                }

        return self.structure

    def _detect_project(self, dirpath: str, dirnames: list[str], filenames: list[str]) -> bool:
        """
        Detect if a directory contains a project.

        Args:
            dirpath: Full path to directory.
            dirnames: List of subdirectory names.
            filenames: List of file names.

        Returns:
            True if project detected, False otherwise.
        """
        all_names = set(filenames) | set(dirnames)
        return bool(PROJECT_INDICATORS & all_names)


def scan_folder(root: Path, exclude_patterns: set[str] | None = None) -> FolderStructure:
    """
    Convenience function to scan a folder.

    Args:
        root: Root directory to scan.
        exclude_patterns: Optional set of patterns to exclude.

    Returns:
        FolderStructure with complete inventory.
    """
    scanner = FolderScanner(root, exclude_patterns)
    return scanner.scan()
