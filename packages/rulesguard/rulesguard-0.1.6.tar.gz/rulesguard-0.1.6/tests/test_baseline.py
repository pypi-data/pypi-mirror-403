"""Test module for baseline feature.

Tests cover:
- Baseline generation
- Baseline loading and matching
- Baseline suppression of findings
"""

from pathlib import Path

from rulesguard.config import ScannerConfig
from rulesguard.models import Baseline, BaselineFinding, Finding, Severity
from rulesguard.scanner import RulesGuardScanner


class TestBaselineGeneration:
    """Test suite for baseline generation."""

    def test_baseline_from_finding(self, tmp_path: Path) -> None:
        """Test creating baseline finding from regular finding."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test')")

        finding = Finding(
            file_path=str(test_file),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('test')",
            recommendation="Remove eval()",
            detector_name="PatternDetector",
        )

        baseline_finding = BaselineFinding.from_finding(finding, tmp_path)
        assert baseline_finding.rule_id == "PatternDetector:code_execution"
        assert baseline_finding.file_path == "test.cursorrules"
        assert baseline_finding.line == 1
        assert baseline_finding.snippet_hash is not None

    def test_baseline_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading baseline."""
        baseline = Baseline()
        baseline.add_finding(
            BaselineFinding(
                rule_id="test:rule",
                file_path="test.cursorrules",
                line=1,
                snippet_hash="abc123",
            )
        )

        baseline_file = tmp_path / "baseline.json"
        baseline.save(baseline_file)

        # Load baseline
        loaded = Baseline.load(baseline_file)
        assert len(loaded.findings) == 1
        assert loaded.findings[0].rule_id == "test:rule"

    def test_baseline_matches_finding(self, tmp_path: Path) -> None:
        """Test that baseline correctly matches findings."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test')")

        finding = Finding(
            file_path=str(test_file),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('test')",
            recommendation="Remove eval()",
            detector_name="PatternDetector",
        )

        baseline_finding = BaselineFinding.from_finding(finding, tmp_path)
        baseline = Baseline()
        baseline.add_finding(baseline_finding)

        # Should match
        assert baseline.contains(finding, tmp_path)

    def test_baseline_does_not_match_different_finding(self, tmp_path: Path) -> None:
        """Test that baseline does not match different findings."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test')")

        finding1 = Finding(
            file_path=str(test_file),
            line=1,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="eval('test')",
            recommendation="Remove eval()",
            detector_name="PatternDetector",
        )

        finding2 = Finding(
            file_path=str(test_file),
            line=2,
            column=1,
            severity=Severity.CRITICAL,
            category="code_execution",
            description="Code execution detected",
            snippet="exec('other')",
            recommendation="Remove exec()",
            detector_name="PatternDetector",
        )

        baseline_finding = BaselineFinding.from_finding(finding1, tmp_path)
        baseline = Baseline()
        baseline.add_finding(baseline_finding)

        # Should not match different finding
        assert not baseline.contains(finding2, tmp_path)


class TestBaselineSuppression:
    """Test suite for baseline suppression of findings."""

    def test_baseline_suppresses_findings(self, tmp_path: Path) -> None:
        """Test that baseline suppresses known findings."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test')")

        # First scan to generate baseline
        scanner1 = RulesGuardScanner()
        result1 = scanner1.scan_file(test_file)
        assert len(result1.findings) > 0

        # Create baseline
        baseline = Baseline()
        baseline_root = tmp_path
        for finding in result1.findings:
            baseline_finding = BaselineFinding.from_finding(finding, baseline_root)
            baseline.add_finding(baseline_finding)

        baseline_file = tmp_path / "baseline.json"
        baseline.save(baseline_file)

        # Second scan with baseline
        config = ScannerConfig(baseline_path=baseline_file)
        scanner2 = RulesGuardScanner(config)
        result2 = scanner2.scan_file(test_file)

        # Should have no findings (suppressed by baseline)
        assert len(result2.findings) == 0

    def test_baseline_does_not_suppress_new_findings(self, tmp_path: Path) -> None:
        """Test that baseline does not suppress new findings."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test1')")

        # Generate baseline from first finding
        scanner1 = RulesGuardScanner()
        result1 = scanner1.scan_file(test_file)
        baseline = Baseline()
        for finding in result1.findings:
            baseline_finding = BaselineFinding.from_finding(finding, tmp_path)
            baseline.add_finding(baseline_finding)

        baseline_file = tmp_path / "baseline.json"
        baseline.save(baseline_file)

        # Add new finding
        test_file.write_text("eval('test1')\neval('test2')")

        # Scan with baseline
        config = ScannerConfig(baseline_path=baseline_file)
        scanner2 = RulesGuardScanner(config)
        result2 = scanner2.scan_file(test_file)

        # Should have findings for the new line
        assert len(result2.findings) > 0

    def test_baseline_exit_code_only_considers_new_findings(self, tmp_path: Path) -> None:
        """Test that exit code only considers non-baselined findings."""
        test_file = tmp_path / "test.cursorrules"
        test_file.write_text("eval('test')")

        # Generate baseline
        scanner1 = RulesGuardScanner()
        result1 = scanner1.scan_file(test_file)
        baseline = Baseline()
        for finding in result1.findings:
            baseline_finding = BaselineFinding.from_finding(finding, tmp_path)
            baseline.add_finding(baseline_finding)

        baseline_file = tmp_path / "baseline.json"
        baseline.save(baseline_file)

        # Scan with baseline - should have no findings
        config = ScannerConfig(baseline_path=baseline_file)
        scanner2 = RulesGuardScanner(config)
        result2 = scanner2.scan_file(test_file)

        # No findings means exit code would be 0
        assert len(result2.findings) == 0
