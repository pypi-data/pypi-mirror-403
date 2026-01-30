"""Test module for SARIF reporter.

Tests cover:
- SARIF export with relative paths
- SARIF export with absolute paths
- Valid JSON output
- Version consistency
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from rulesguard.reporters.sarif import SARIFReporter
from rulesguard.models import Finding, ScanResult, ScanSummary, Severity
from rulesguard import __version__


class TestSARIFReporter:
    """Test suite for SARIFReporter."""

    @pytest.fixture
    def reporter(self) -> SARIFReporter:
        """Create SARIF reporter instance.

        Returns:
            SARIFReporter instance
        """
        return SARIFReporter()

    @pytest.fixture
    def sample_finding_relative(self, tmp_path: Path) -> Finding:
        """Create a finding with a relative path.

        Args:
            tmp_path: Temporary directory fixture

        Returns:
            Finding with relative file path
        """
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('malicious')")
        # Use relative path from tmp_path (simulating relative scan)
        relative_path = test_file.relative_to(tmp_path)
        return Finding(
            file_path=str(relative_path),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('malicious')",
            recommendation="Remove eval() usage",
            detector_name="PatternDetector",
        )

    @pytest.fixture
    def sample_finding_absolute(self, tmp_path: Path) -> Finding:
        """Create a finding with an absolute path.

        Args:
            tmp_path: Temporary directory fixture

        Returns:
            Finding with absolute file path
        """
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('malicious')")
        return Finding(
            file_path=str(test_file.resolve()),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('malicious')",
            recommendation="Remove eval() usage",
            detector_name="PatternDetector",
        )

    def test_sarif_export_relative_path(self, reporter: SARIFReporter, tmp_path: Path) -> None:
        """Test that SARIF export works with relative paths and does not crash.

        Args:
            reporter: SARIF reporter instance
            tmp_path: Temporary directory fixture
        """
        # Create a test file and use relative path from tmp_path
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('malicious')")
        relative_path = test_file.relative_to(tmp_path)
        
        finding = Finding(
            file_path=str(relative_path),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('malicious')",
            recommendation="Remove eval() usage",
            detector_name="PatternDetector",
        )
        
        # Create scan summary with relative path finding
        result = ScanResult(file_path=str(relative_path))
        result.findings = [finding]
        summary = ScanSummary()
        summary.add_result(result)

        # Change to tmp_path directory to simulate relative path scenario
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            # Export to SARIF - should not crash
            output_file = tmp_path / "output.sarif"
            reporter.export(summary, str(output_file))
        finally:
            os.chdir(old_cwd)

        # Verify file was created
        assert output_file.exists(), "SARIF file should be created"

        # Verify it's valid JSON
        with open(output_file, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)

        # Verify structure
        assert "version" in sarif_data
        assert "runs" in sarif_data
        assert len(sarif_data["runs"]) > 0

        # Verify URI is absolute (not relative)
        run = sarif_data["runs"][0]
        assert "results" in run
        if run["results"]:
            result_obj = run["results"][0]
            assert "locations" in result_obj
            location = result_obj["locations"][0]
            uri = location["physicalLocation"]["artifactLocation"]["uri"]
            # URI should be absolute (file:/// on Windows, file:// on Unix)
            assert uri.startswith("file://"), f"URI should be absolute, got: {uri}"

    def test_sarif_export_absolute_path(self, reporter: SARIFReporter, sample_finding_absolute: Finding, tmp_path: Path) -> None:
        """Test that SARIF export works with absolute paths.

        Args:
            reporter: SARIF reporter instance
            sample_finding_absolute: Finding with absolute path
            tmp_path: Temporary directory fixture
        """
        # Create scan summary with absolute path finding
        result = ScanResult(file_path=sample_finding_absolute.file_path)
        result.findings = [sample_finding_absolute]
        summary = ScanSummary()
        summary.add_result(result)

        # Export to SARIF
        output_file = tmp_path / "output.sarif"
        reporter.export(summary, str(output_file))

        # Verify file was created and is valid JSON
        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)

        # Verify URI is absolute
        run = sarif_data["runs"][0]
        if run["results"]:
            result_obj = run["results"][0]
            uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            assert uri.startswith("file://"), f"URI should be absolute, got: {uri}"

    def test_sarif_valid_json(self, reporter: SARIFReporter, sample_finding_absolute: Finding, tmp_path: Path) -> None:
        """Test that SARIF output is valid JSON.

        Args:
            reporter: SARIF reporter instance
            sample_finding_absolute: Finding with absolute path
            tmp_path: Temporary directory fixture
        """
        result = ScanResult(file_path=sample_finding_absolute.file_path)
        result.findings = [sample_finding_absolute]
        summary = ScanSummary()
        summary.add_result(result)

        output_file = tmp_path / "output.sarif"
        reporter.export(summary, str(output_file))

        # Verify valid JSON
        with open(output_file, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)

        # Verify required SARIF fields
        assert sarif_data["version"] == "2.1.0"
        assert "$schema" in sarif_data
        assert "runs" in sarif_data
        assert len(sarif_data["runs"]) == 1

        run = sarif_data["runs"][0]
        assert "tool" in run
        assert "driver" in run["tool"]
        assert run["tool"]["driver"]["name"] == "RulesGuard"

    def test_sarif_version_consistency(self, reporter: SARIFReporter) -> None:
        """Test that SARIF reporter uses correct version from package.

        Args:
            reporter: SARIF reporter instance
        """
        # Version should match package version
        assert reporter.tool_version == __version__, f"SARIF version {reporter.tool_version} should match package version {__version__}"

    def test_sarif_export_from_relative_scan_path(self, reporter: SARIFReporter, tmp_path: Path) -> None:
        """Test SARIF export when scanning with a relative path.

        This simulates the real-world scenario where a user runs:
        `rulesguard .` from a subdirectory, which creates relative paths.

        Args:
            reporter: SARIF reporter instance
            tmp_path: Temporary directory fixture
        """
        # Create a test file in a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.cursorrules"
        test_file.write_text("eval('test')")

        # Create finding with relative path (simulating scan from parent directory)
        relative_path = test_file.relative_to(tmp_path)
        finding = Finding(
            file_path=str(relative_path),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('test')",
            recommendation="Remove eval() usage",
            detector_name="PatternDetector",
        )

        result = ScanResult(file_path=str(relative_path))
        result.findings = [finding]
        summary = ScanSummary()
        summary.add_result(result)

        # Change to tmp_path to simulate relative path scenario
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            # Export to SARIF - should not crash
            output_file = tmp_path / "output.sarif"
            reporter.export(summary, str(output_file))
        finally:
            os.chdir(old_cwd)

        # Verify valid JSON and absolute URIs
        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)

        # Verify URI is absolute
        run = sarif_data["runs"][0]
        if run["results"]:
            uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            assert uri.startswith("file://"), f"URI should be absolute even from relative path, got: {uri}"
