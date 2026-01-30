"""Base detector class for RulesGuard.

All security detectors must inherit from this abstract base class
to ensure consistent interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from ..models import Finding


class BaseDetector(ABC):
    """Abstract base class for all security detectors.

    All detectors must implement the detect() method and provide
    a name property. Detectors are designed to be stateless and
    thread-safe for parallel execution.
    """

    @abstractmethod
    def detect(self, content: str, filepath: str) -> List[Finding]:
        """Detect security issues in file content.

        Args:
            content: File content to scan
            filepath: Path to the file being scanned (for context)

        Returns:
            List of Finding objects representing detected threats

        Raises:
            ValueError: If content or filepath is invalid
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this detector.

        Returns:
            Detector name (e.g., "UnicodeDetector", "PatternDetector")
        """
        pass

    def _validate_input(self, content: str, filepath: str) -> None:
        """Validate detector input parameters.

        Args:
            content: File content to validate
            filepath: File path to validate

        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        if not isinstance(filepath, (str, Path)):
            raise ValueError("Filepath must be a string or Path object")
        if not filepath:
            raise ValueError("Filepath cannot be empty")

    def _get_line_number(self, content: str, position: int) -> int:
        """Calculate line number from character position.

        Args:
            content: File content
            position: Character position (0-indexed)

        Returns:
            Line number (1-indexed)
        """
        if position < 0 or position >= len(content):
            return 1
        return content[:position].count("\n") + 1

    def _get_column_number(self, content: str, position: int) -> int:
        """Calculate column number from character position.

        Args:
            content: File content
            position: Character position (0-indexed)

        Returns:
            Column number (1-indexed)
        """
        if position < 0 or position >= len(content):
            return 1
        last_newline = content.rfind("\n", 0, position)
        return position - last_newline

    def _get_snippet(
        self, content: str, start: int, end: int, context_lines: int = 2
    ) -> str:
        """Extract code snippet with context.

        Args:
            content: File content
            start: Start position (0-indexed)
            end: End position (0-indexed)
            context_lines: Number of context lines to include

        Returns:
            Code snippet with surrounding context
        """
        lines = content.split("\n")
        start_line = self._get_line_number(content, start) - 1
        end_line = self._get_line_number(content, end) - 1

        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)

        snippet_lines = lines[context_start:context_end]
        return "\n".join(snippet_lines)
