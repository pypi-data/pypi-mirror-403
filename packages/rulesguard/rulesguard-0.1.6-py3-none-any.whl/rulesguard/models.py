"""Data models for RulesGuard scanner.

This module defines the core data structures used throughout the scanner,
including findings, severity levels, and scan results.
"""

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


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
        cve_ref: Optional CVE reference (e.g., "CVE-2021-42574")
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
    findings: list[Finding] = field(default_factory=list)
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
    results: list[ScanResult] = field(default_factory=list)

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


@dataclass
class BaselineFinding:
    """Represents a finding in the baseline.

    Attributes:
        rule_id: Identifier for the rule/detector pattern
        file_path: Path to the file (relative to baseline root)
        line: Line number where finding occurs
        snippet_hash: Hash of the matched snippet for stability
    """

    rule_id: str
    file_path: str
    line: int
    snippet_hash: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "rule_id": self.rule_id,
            "file_path": self.file_path,
            "line": self.line,
            "snippet_hash": self.snippet_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineFinding":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            BaselineFinding instance
        """
        return cls(
            rule_id=data["rule_id"],
            file_path=data["file_path"],
            line=data["line"],
            snippet_hash=data["snippet_hash"],
        )

    @classmethod
    def from_finding(cls, finding: Finding, baseline_root: Path) -> "BaselineFinding":
        """Create baseline finding from a regular finding.

        Args:
            finding: Finding to convert
            baseline_root: Root path for relative file paths

        Returns:
            BaselineFinding instance
        """
        # Create rule_id from detector and category
        rule_id = f"{finding.detector_name}:{finding.category}"

        # Get relative file path
        try:
            file_path_obj = Path(finding.file_path)
            if file_path_obj.is_absolute():
                try:
                    rel_path = file_path_obj.relative_to(baseline_root)
                    file_path = str(rel_path)
                except ValueError:
                    file_path = finding.file_path
            else:
                file_path = finding.file_path
        except Exception:
            file_path = finding.file_path

        # Hash the snippet for stability
        snippet_hash = hashlib.sha256(finding.snippet.encode("utf-8")).hexdigest()[:16]

        return cls(
            rule_id=rule_id,
            file_path=file_path,
            line=finding.line,
            snippet_hash=snippet_hash,
        )

    def matches(self, finding: Finding, baseline_root: Path) -> bool:
        """Check if a finding matches this baseline entry.

        Args:
            finding: Finding to check
            baseline_root: Root path for relative file paths

        Returns:
            True if finding matches baseline, False otherwise
        """
        # Check rule_id
        rule_id = f"{finding.detector_name}:{finding.category}"
        if rule_id != self.rule_id:
            return False

        # Check file path
        try:
            file_path_obj = Path(finding.file_path)
            if file_path_obj.is_absolute():
                try:
                    rel_path = file_path_obj.relative_to(baseline_root)
                    file_path = str(rel_path)
                except ValueError:
                    file_path = finding.file_path
            else:
                file_path = finding.file_path
        except Exception:
            file_path = finding.file_path

        if file_path != self.file_path:
            return False

        # Check line number
        if finding.line != self.line:
            return False

        # Check snippet hash
        snippet_hash = hashlib.sha256(finding.snippet.encode("utf-8")).hexdigest()[:16]
        if snippet_hash != self.snippet_hash:
            return False

        return True


@dataclass
class Baseline:
    """Baseline of known findings to suppress in future scans.

    Attributes:
        version: Baseline format version
        findings: List of baseline findings
    """

    version: str = "1.0"
    findings: list[BaselineFinding] = field(default_factory=list)

    def add_finding(self, finding: BaselineFinding) -> None:
        """Add a finding to the baseline.

        Args:
            finding: Finding to add
        """
        self.findings.append(finding)

    def contains(self, finding: Finding, baseline_root: Path) -> bool:
        """Check if a finding is in the baseline.

        Args:
            finding: Finding to check
            baseline_root: Root path for relative file paths

        Returns:
            True if finding is in baseline, False otherwise
        """
        for baseline_finding in self.findings:
            if baseline_finding.matches(finding, baseline_root):
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "findings": [f.to_dict() for f in self.findings],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Baseline":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Baseline instance
        """
        findings = [BaselineFinding.from_dict(f) for f in data.get("findings", [])]
        return cls(version=data.get("version", "1.0"), findings=findings)

    def save(self, path: Path) -> None:
        """Save baseline to file.

        Args:
            path: Path to save baseline file
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Baseline":
        """Load baseline from file.

        Args:
            path: Path to baseline file

        Returns:
            Baseline instance
        """
        if not path.exists():
            return cls()

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return cls.from_dict(data)
