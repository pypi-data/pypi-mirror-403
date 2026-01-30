"""Test module for CLI exit code behavior.

Tests cover:
- Exit code behavior with --fail-on option
- Exit codes for different severity thresholds
- Exit codes for different output formats
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIExitCodes:
    """Test suite for CLI exit code behavior."""

    @pytest.fixture
    def malicious_file(self, tmp_path: Path) -> Path:
        """Create a temporary file with CRITICAL findings.

        Args:
            tmp_path: Temporary directory fixture

        Returns:
            Path to temporary file with CRITICAL findings
        """
        test_file = tmp_path / "test.cursorrules"
        # Content that will trigger CRITICAL findings (eval)
        test_file.write_text("eval('malicious code')")
        return test_file

    @pytest.fixture
    def low_severity_file(self, tmp_path: Path) -> Path:
        """Create a temporary file with LOW findings.

        Args:
            tmp_path: Temporary directory fixture

        Returns:
            Path to temporary file with LOW findings
        """
        test_file = tmp_path / "test_low.cursorrules"
        # Content that may trigger LOW findings (hex encoding)
        test_file.write_text("0x" + "a" * 100)
        return test_file

    def test_exit_code_critical_findings_default(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 1 for CRITICAL findings (default threshold)."""
        # Test default behavior (backward compatibility: "rulesguard .")
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Should exit with code 1 for CRITICAL findings"

    def test_exit_code_critical_findings_explicit(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 1 when --fail-on critical and CRITICAL findings exist."""
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file), "--fail-on", "critical"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Should exit with code 1 for CRITICAL findings"

    def test_exit_code_high_findings(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 1 when --fail-on high and CRITICAL findings exist."""
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file), "--fail-on", "high"],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 1
        ), "Should exit with code 1 when threshold is high and CRITICAL findings exist"

    def test_exit_code_medium_findings(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 1 when --fail-on medium and CRITICAL findings exist."""
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file), "--fail-on", "medium"],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 1
        ), "Should exit with code 1 when threshold is medium and CRITICAL findings exist"

    def test_exit_code_low_findings(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 1 when --fail-on low and CRITICAL findings exist."""
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file), "--fail-on", "low"],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 1
        ), "Should exit with code 1 when threshold is low and CRITICAL findings exist"

    def test_exit_code_none_never_fails(self, malicious_file: Path) -> None:
        """Test that CLI exits with code 0 when --fail-on none even with findings."""
        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(malicious_file), "--fail-on", "none"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Should exit with code 0 when --fail-on none"

    def test_exit_code_json_format(self, malicious_file: Path) -> None:
        """Test that exit codes work with JSON output format."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "rulesguard.cli",
                str(malicious_file),
                "--format",
                "json",
                "--fail-on",
                "critical",
            ],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 1
        ), "Should exit with code 1 for JSON format with CRITICAL findings"

    def test_exit_code_sarif_format(self, malicious_file: Path) -> None:
        """Test that exit codes work with SARIF output format."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "rulesguard.cli",
                str(malicious_file),
                "--format",
                "sarif",
                "--fail-on",
                "critical",
            ],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 1
        ), "Should exit with code 1 for SARIF format with CRITICAL findings"

    def test_exit_code_clean_file(self, tmp_path: Path) -> None:
        """Test that CLI exits with code 0 for clean files."""
        clean_file = tmp_path / "clean.cursorrules"
        clean_file.write_text("# Clean file\n# No malicious patterns")

        result = subprocess.run(
            [sys.executable, "-m", "rulesguard.cli", str(clean_file), "--fail-on", "critical"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Should exit with code 0 for clean files"
