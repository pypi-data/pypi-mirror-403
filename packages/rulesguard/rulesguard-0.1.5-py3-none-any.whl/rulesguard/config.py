"""Configuration management for RulesGuard.

Handles scanner configuration, detector selection, and file filtering.
"""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


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
    ignore_patterns: List[str] = field(default_factory=list)
    baseline_path: Optional[Path] = None

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
            "dist",
        }
    )
    
    # Directory patterns to exclude (checked against path parts)
    EXCLUDE_DIR_PATTERNS: Set[str] = field(
        default_factory=lambda: {
            "tests/fixtures",
            ".cursor",
        }
    )

    @classmethod
    def load_ignore_file(cls, scan_root: Path) -> List[str]:
        """Load ignore patterns from .rulesguardignore file.

        Args:
            scan_root: Root directory to look for .rulesguardignore

        Returns:
            List of glob patterns to ignore
        """
        ignore_file = scan_root / ".rulesguardignore"
        if not ignore_file.exists():
            return []

        patterns: List[str] = []
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip blank lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            # If we can't read the file, return empty list
            pass

        return patterns

    def should_scan_file(self, file_path: Path, scan_root: Optional[Path] = None, ignore_patterns: Optional[List[str]] = None) -> bool:
        """Check if a file should be scanned.

        Args:
            file_path: Path to check
            scan_root: Root directory being scanned (for exclude pattern logic)
            ignore_patterns: Optional ignore patterns (overrides self.ignore_patterns)

        Returns:
            True if file should be scanned, False otherwise
        """
        patterns_to_check = ignore_patterns if ignore_patterns is not None else self.ignore_patterns
        # Check ignore patterns from .rulesguardignore
        if scan_root is not None:
            for pattern in patterns_to_check:
                # Convert pattern to match against file path relative to scan_root
                try:
                    rel_path = file_path.relative_to(scan_root)
                    # Use fnmatch for glob pattern matching
                    if fnmatch.fnmatch(str(rel_path), pattern) or fnmatch.fnmatch(rel_path.name, pattern):
                        return False
                    # Also check against path parts
                    for part in rel_path.parts:
                        if fnmatch.fnmatch(part, pattern):
                            return False
                except ValueError:
                    # Path not relative to scan_root, try absolute matching
                    if fnmatch.fnmatch(str(file_path), pattern) or fnmatch.fnmatch(file_path.name, pattern):
                        return False

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
        file_path_str = str(file_path)
        for pattern in self.EXCLUDE_PATTERNS:
            # Check if pattern matches file name or appears in path
            if pattern in file_path_str or pattern in file_path.name:
                return False
            # Check if any parent directory matches the pattern
            for parent in file_path.parents:
                if pattern in str(parent) or pattern in parent.name:
                    return False
        
        # Check exclude directory patterns (more precise matching)
        # Only exclude if the pattern is a subdirectory of scan_root, not if scan_root is the pattern itself
        file_path_str_normalized = file_path_str.replace("\\", "/")
        for dir_pattern in self.EXCLUDE_DIR_PATTERNS:
            pattern_parts = dir_pattern.split("/")
            file_parts = list(file_path.parts)
            
            # If scan_root is provided and matches the exclude pattern, don't exclude
            # This allows explicit scanning of excluded directories
            if scan_root is not None:
                try:
                    scan_root_str = str(scan_root.resolve()).replace("\\", "/")
                    scan_root_parts = list(scan_root.resolve().parts)
                    # Check if scan_root ends with the exclude pattern
                    if len(scan_root_parts) >= len(pattern_parts):
                        if scan_root_parts[-len(pattern_parts):] == pattern_parts:
                            # scan_root is the excluded directory itself - don't exclude
                            continue
                except (OSError, ValueError):
                    pass
            
            # Check if pattern parts appear consecutively in file path
            for i in range(len(file_parts) - len(pattern_parts) + 1):
                if file_parts[i:i+len(pattern_parts)] == pattern_parts:
                    # Found the pattern - exclude this file
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
