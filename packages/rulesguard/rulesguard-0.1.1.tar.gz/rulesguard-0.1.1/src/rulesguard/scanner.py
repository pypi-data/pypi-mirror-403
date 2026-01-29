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
from .models import Finding, ScanResult, ScanSummary

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

    def scan_file(self, file_path: Path) -> ScanResult:
        """Scan a single file for security threats.

        Args:
            file_path: Path to file to scan

        Returns:
            ScanResult with findings and risk score
        """
        result = ScanResult(file_path=str(file_path))

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

            result.findings = all_findings

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

        if path.is_file():
            # Scan single file
            if self.config.should_scan_file(path):
                result = self.scan_file(path)
                summary.add_result(result)
        elif path.is_dir():
            # Scan directory
            if self.config.recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in path.glob(pattern):
                if file_path.is_file() and self.config.should_scan_file(file_path):
                    result = self.scan_file(file_path)
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
