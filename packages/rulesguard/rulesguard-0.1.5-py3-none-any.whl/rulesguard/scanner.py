"""Main scanner orchestration for RulesGuard.

Coordinates all detectors to scan files and directories for security threats.
"""

import logging
from pathlib import Path
from typing import List, Optional

from .config import ScannerConfig
from .detectors.base import BaseDetector
from .detectors.unicode import UnicodeDetector
from .detectors.pattern import PatternDetector
from .detectors.entropy import EntropyDetector
from .models import Baseline, Finding, ScanResult, ScanSummary

logger = logging.getLogger(__name__)


class RulesGuardScanner:
    """Main scanner for detecting security threats in configuration files."""

    def __init__(self, config: Optional[ScannerConfig] = None) -> None:
        """Initialize scanner with configuration.

        Args:
            config: Scanner configuration (uses default if None)
        """
        self.config = config or ScannerConfig()
        self.detectors: List[BaseDetector] = []
        self.baseline: Optional[Baseline] = None

        # Load baseline if provided
        if self.config.baseline_path:
            self.baseline = Baseline.load(self.config.baseline_path)

        # Initialize detectors
        self._initialize_detectors()

    def _initialize_detectors(self) -> None:
        """Initialize all available detectors.

        Filters detectors based on config.detectors if specified.
        """
        all_detectors: List[BaseDetector] = [
            UnicodeDetector(),
            PatternDetector(),
            EntropyDetector(),
        ]

        if self.config.detectors:
            # Filter to only enabled detectors
            # Match detector names without "Detector" suffix (e.g., "unicode" matches "UnicodeDetector")
            enabled_names = {d.lower() for d in self.config.detectors}
            self.detectors = [
                d
                for d in all_detectors
                if d.name.lower().replace("detector", "") in enabled_names
            ]
        else:
            # Use all detectors
            self.detectors = all_detectors

        logger.info(f"Initialized {len(self.detectors)} detector(s)")

    def _is_ignored_by_pragma(self, finding: Finding, content_lines: List[str]) -> bool:
        """Check if a finding is suppressed by an inline ignore pragma.

        Args:
            finding: Finding to check
            content_lines: List of file content lines (0-indexed)

        Returns:
            True if finding should be ignored, False otherwise
        """
        # Check if line number is valid
        if finding.line < 1 or finding.line > len(content_lines):
            return False

        # Check current line (1-indexed -> 0-indexed)
        current_line_idx = finding.line - 1
        current_line = content_lines[current_line_idx]

        # Check for pragma on same line
        if "rulesguard: ignore" in current_line.lower():
            return True

        # Check for pragma on previous line
        if current_line_idx > 0:
            prev_line = content_lines[current_line_idx - 1]
            if "rulesguard: ignore" in prev_line.lower():
                return True

        return False

    def _is_in_baseline(self, finding: Finding, file_path: Path) -> bool:
        """Check if a finding is in the baseline.

        Args:
            finding: Finding to check
            file_path: Path to the file

        Returns:
            True if finding is in baseline, False otherwise
        """
        if not self.baseline:
            return False

        # Determine baseline root (parent of baseline file or current working directory)
        if self.config.baseline_path:
            baseline_root = self.config.baseline_path.parent
        else:
            baseline_root = Path.cwd()

        return self.baseline.contains(finding, baseline_root)

    def scan_file(self, file_path: Path, skip_should_scan_check: bool = False) -> ScanResult:
        """Scan a single file for security threats.

        Args:
            file_path: Path to file to scan
            skip_should_scan_check: If True, skip the should_scan_file check (for direct scanning)

        Returns:
            ScanResult with findings and risk score
        """
        result = ScanResult(file_path=str(file_path))
        
        # Check if file should be scanned (unless explicitly skipped)
        if not skip_should_scan_check:
            if not self.config.should_scan_file(file_path, scan_root=file_path.parent):
                result.scanned = False
                result.error = "File does not match scan patterns"
                return result

        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                result.scanned = False
                result.error = f"File too large ({file_size} bytes > {self.config.max_file_size})"
                return result

            # Read file content
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                result.scanned = False
                result.error = f"Failed to read file: {e}"
                return result

            # Run all detectors
            all_findings: List[Finding] = []
            for detector in self.detectors:
                try:
                    findings = detector.detect(content, str(file_path))
                    all_findings.extend(findings)
                except Exception as e:
                    logger.warning(f"Detector {detector.name} failed: {e}")
                    continue

            # Filter findings based on inline ignore pragmas and baseline
            content_lines = content.splitlines()
            filtered_findings: List[Finding] = []
            for finding in all_findings:
                # Skip if ignored by pragma
                if self._is_ignored_by_pragma(finding, content_lines):
                    continue
                # Skip if in baseline
                if self.baseline is not None and self._is_in_baseline(finding, file_path):
                    continue
                filtered_findings.append(finding)

            result.findings = filtered_findings

            # Calculate risk score
            is_system_file = self.config.is_system_file(file_path)
            has_unicode = any(f.category.startswith("unicode") for f in all_findings)
            has_pattern = any(
                f.category
                in {
                    "code_execution",
                    "shell_injection",
                    "remote_import",
                    "credential_theft",
                }
                for f in all_findings
            )
            has_unicode_and_pattern = has_unicode and has_pattern

            result.calculate_risk_score(
                is_system_file=is_system_file,
                has_unicode_and_pattern=has_unicode_and_pattern,
            )

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            result.scanned = False
            result.error = str(e)

        return result

    def scan_path(self, path: Path) -> ScanSummary:
        """Scan a file or directory for security threats.

        Args:
            path: Path to file or directory to scan

        Returns:
            ScanSummary with results from all scanned files
        """
        summary = ScanSummary()

        # Load ignore patterns from .rulesguardignore if scanning a directory
        scan_root = path if path.is_dir() else path.parent
        ignore_patterns: List[str] = []
        if scan_root.exists():
            ignore_patterns = ScannerConfig.load_ignore_file(scan_root)

        if path.is_file():
            # Scan single file
            if self.config.should_scan_file(path, scan_root=path.parent, ignore_patterns=ignore_patterns):
                result = self.scan_file(path, skip_should_scan_check=True)
                summary.add_result(result)
        elif path.is_dir():
            # Scan directory
            if self.config.recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in path.glob(pattern):
                if file_path.is_file() and self.config.should_scan_file(file_path, scan_root=path, ignore_patterns=ignore_patterns):
                    result = self.scan_file(file_path, skip_should_scan_check=True)
                    summary.add_result(result)
        else:
            logger.warning(f"Path does not exist: {path}")

        return summary

    def scan(self) -> ScanSummary:
        """Scan all configured target paths.

        Returns:
            ScanSummary with results from all scanned files
        """
        summary = ScanSummary()

        for target_path in self.config.target_paths:
            path_summary = self.scan_path(target_path)
            # Merge results
            for result in path_summary.results:
                summary.add_result(result)

        return summary
