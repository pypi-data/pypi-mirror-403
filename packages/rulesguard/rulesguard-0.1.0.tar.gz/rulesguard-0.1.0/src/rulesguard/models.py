"""Data models for RulesGuard scanner.

This module defines the core data structures used throughout the scanner,
including findings, severity levels, and scan results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from pathlib import Path


class Severity(Enum):
    """Severity levels for security findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def score(self) -> int:
        """Return the risk score points for this severity level.

        Returns:
            Risk score points (25 for CRITICAL, 15 for HIGH, 8 for MEDIUM, 3 for LOW)
        """
        score_map = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
        }
        return score_map[self]


@dataclass
class Finding:
    """Represents a security finding detected in a file.

    Attributes:
        file_path: Path to the file where the finding was detected
        line: Line number (1-indexed) where the finding occurs
        column: Column number (1-indexed) where the finding starts
        severity: Severity level of the finding
        category: Category of the threat (e.g., "unicode", "code_execution")
        description: Human-readable description of the threat
        snippet: Code snippet showing the problematic code
        recommendation: Recommended remediation steps
        cve_ref: Optional CVE reference (e.g., "CVE-2026-21858")
        detector_name: Name of the detector that found this issue
    """

    file_path: str
    line: int
    column: int
    severity: Severity
    category: str
    description: str
    snippet: str
    recommendation: str
    cve_ref: Optional[str] = None
    detector_name: str = "unknown"

    def __post_init__(self) -> None:
        """Validate finding data after initialization."""
        if self.line < 1:
            raise ValueError("Line number must be >= 1")
        if self.column < 1:
            raise ValueError("Column number must be >= 1")
        if not self.description:
            raise ValueError("Description cannot be empty")
        if not self.category:
            raise ValueError("Category cannot be empty")


@dataclass
class ScanResult:
    """Results from scanning a file or directory.

    Attributes:
        file_path: Path to the scanned file
        findings: List of security findings
        risk_score: Calculated risk score (0-100)
        scanned: Whether the file was successfully scanned
        error: Error message if scanning failed
    """

    file_path: str
    findings: List[Finding] = field(default_factory=list)
    risk_score: int = 0
    scanned: bool = True
    error: Optional[str] = None

    def calculate_risk_score(
        self,
        is_system_file: bool = False,
        has_unicode_and_pattern: bool = False,
    ) -> int:
        """Calculate risk score based on findings.

        Risk score formula:
        - Base: sum of severity scores
        - Multiplier 1.2x if multiple findings in same file
        - Multiplier 1.5x if in system files (.vscode/, .github/)
        - Multiplier 2.0x if Unicode + pattern match found together

        Args:
            is_system_file: Whether file is in a system directory
            has_unicode_and_pattern: Whether both Unicode and pattern threats found

        Returns:
            Risk score from 0-100 (capped at 100)
        """
        if not self.findings:
            return 0

        base_score = sum(finding.severity.score() for finding in self.findings)

        multiplier = 1.0
        if len(self.findings) > 1:
            multiplier *= 1.2
        if is_system_file:
            multiplier *= 1.5
        if has_unicode_and_pattern:
            multiplier *= 2.0

        self.risk_score = min(100, int(base_score * multiplier))
        return self.risk_score

    @property
    def has_findings(self) -> bool:
        """Check if any findings were detected.

        Returns:
            True if findings exist, False otherwise
        """
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        """Count of CRITICAL severity findings.

        Returns:
            Number of CRITICAL findings
        """
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count of HIGH severity findings.

        Returns:
            Number of HIGH findings
        """
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        """Count of MEDIUM severity findings.

        Returns:
            Number of MEDIUM findings
        """
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Count of LOW severity findings.

        Returns:
            Number of LOW findings
        """
        return sum(1 for f in self.findings if f.severity == Severity.LOW)


@dataclass
class ScanSummary:
    """Summary of scanning multiple files.

    Attributes:
        total_files: Total number of files scanned
        files_with_findings: Number of files with security findings
        total_findings: Total number of findings across all files
        critical_files: Number of files with CRITICAL findings
        max_risk_score: Highest risk score found
        results: List of individual scan results
    """

    total_files: int = 0
    files_with_findings: int = 0
    total_findings: int = 0
    critical_files: int = 0
    max_risk_score: int = 0
    results: List[ScanResult] = field(default_factory=list)

    def add_result(self, result: ScanResult) -> None:
        """Add a scan result to the summary.

        Args:
            result: Scan result to add
        """
        self.results.append(result)
        self.total_files += 1

        if result.has_findings:
            self.files_with_findings += 1
            self.total_findings += len(result.findings)

            if result.critical_count > 0:
                self.critical_files += 1

            if result.risk_score > self.max_risk_score:
                self.max_risk_score = result.risk_score
