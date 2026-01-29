"""Configuration management for RulesGuard.

Handles scanner configuration, detector selection, and file filtering.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class ScannerConfig:
    """Configuration for RulesGuard scanner.

    Attributes:
        target_paths: Paths to scan (files or directories)
        detectors: List of detector names to enable (empty = all)
        exclude_paths: Paths to exclude from scanning
        max_file_size: Maximum file size to scan in bytes (default 10MB)
        follow_symlinks: Whether to follow symbolic links
        recursive: Whether to scan directories recursively
    """

    target_paths: List[Path] = field(default_factory=list)
    detectors: List[str] = field(default_factory=list)
    exclude_paths: List[Path] = field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    follow_symlinks: bool = False
    recursive: bool = True

    # File patterns to scan
    SCAN_PATTERNS: Set[str] = field(
        default_factory=lambda: {
            "*.cursorrules",
            "*.mdc",
            ".cursorrules",
            ".vscode/settings.json",
            ".vscode/settings.jsonc",
            ".idea/**/*.xml",
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
        }
    )

    # File patterns to exclude
    EXCLUDE_PATTERNS: Set[str] = field(
        default_factory=lambda: {
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
        }
    )

    def should_scan_file(self, file_path: Path) -> bool:
        """Check if a file should be scanned.

        Args:
            file_path: Path to check

        Returns:
            True if file should be scanned, False otherwise
        """
        # Check if explicitly excluded
        for exclude_path in self.exclude_paths:
            try:
                if file_path.resolve() == exclude_path.resolve():
                    return False
                if exclude_path.resolve() in file_path.resolve().parents:
                    return False
            except (OSError, ValueError):
                # Path resolution failed, skip
                continue

        # Check exclude patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern in str(file_path) or pattern in file_path.name:
                return False

        # Check if matches scan patterns
        for pattern in self.SCAN_PATTERNS:
            if pattern in str(file_path) or file_path.match(pattern):
                return True

        # Default: scan common config files
        config_names = {
            ".cursorrules",
            ".vscode/settings.json",
            ".vscode/settings.jsonc",
            "settings.json",
        }
        return file_path.name in config_names or ".cursor" in str(file_path)

    def is_system_file(self, file_path: Path) -> bool:
        """Check if file is in a system directory.

        Args:
            file_path: Path to check

        Returns:
            True if file is in .vscode/, .github/, or similar system directories
        """
        parts = file_path.parts
        system_dirs = {".vscode", ".github", ".idea", ".cursor", ".git"}
        return any(part in system_dirs for part in parts)
