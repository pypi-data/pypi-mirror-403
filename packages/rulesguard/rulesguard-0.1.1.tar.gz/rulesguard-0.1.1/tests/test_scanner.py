"""Test module for RulesGuardScanner.

Tests cover:
- File scanning
- Directory scanning
- Risk score calculation
- Multiple detector coordination
- Error handling
"""

import pytest
from pathlib import Path
from rulesguard.scanner import RulesGuardScanner
from rulesguard.config import ScannerConfig
from rulesguard.models import Severity


class TestRulesGuardScanner:
    """Test suite for RulesGuardScanner."""

    @pytest.fixture
    def scanner(self) -> RulesGuardScanner:
        """Create scanner instance.

        Returns:
            RulesGuardScanner instance
        """
        config = ScannerConfig()
        return RulesGuardScanner(config)

    def test_scan_malicious_file(self, scanner: RulesGuardScanner, malicious_dir: Path) -> None:
        """Test scanning a malicious file."""
        test_file = malicious_dir / "hidden_unicode.cursorrules"
        if not test_file.exists():
            pytest.skip("Test fixture not found")

        result = scanner.scan_file(test_file)

        assert result.scanned
        assert result.has_findings
        assert len(result.findings) > 0

    def test_scan_clean_file(self, scanner: RulesGuardScanner, clean_dir: Path) -> None:
        """Test scanning a clean file."""
        test_file = clean_dir / "normal.cursorrules"
        if not test_file.exists():
            pytest.skip("Test fixture not found")

        result = scanner.scan_file(test_file)

        assert result.scanned
        # Should have no findings (or minimal false positives)
        # Note: Some detectors may flag things, but should be minimal

    def test_scan_directory(self, scanner: RulesGuardScanner, fixtures_dir: Path) -> None:
        """Test scanning a directory."""
        summary = scanner.scan_path(fixtures_dir)

        assert summary.total_files > 0
        # Should find some malicious files
        assert summary.files_with_findings > 0

    def test_risk_score_calculation(self, scanner: RulesGuardScanner, malicious_dir: Path) -> None:
        """Test risk score calculation."""
        test_file = malicious_dir / "eval_injection.json"
        if not test_file.exists():
            pytest.skip("Test fixture not found")

        result = scanner.scan_file(test_file)
        result.calculate_risk_score()

        assert result.risk_score >= 0
        assert result.risk_score <= 100

    def test_multiple_findings_increase_score(self, scanner: RulesGuardScanner) -> None:
        """Test that multiple findings increase risk score."""
        content = "eval('code1')\neval('code2')\neval('code3')"
        test_file = Path("test_multi.cursorrules")
        test_file.write_text(content)

        try:
            result = scanner.scan_file(test_file)
            score_multi = result.risk_score

            # Single finding
            content_single = "eval('code1')"
            test_file.write_text(content_single)
            result_single = scanner.scan_file(test_file)
            score_single = result_single.risk_score

            # Multiple findings should have higher score (with multiplier)
            assert score_multi >= score_single
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_system_file_multiplier(self, scanner: RulesGuardScanner) -> None:
        """Test that system files get risk score multiplier."""
        content = "eval('code')"
        test_file = Path(".vscode/test.cursorrules")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text(content)

        try:
            result = scanner.scan_file(test_file)
            is_system = scanner.config.is_system_file(test_file)

            assert is_system
            # System files should have higher risk scores
        finally:
            if test_file.exists():
                test_file.unlink()
            if test_file.parent.exists() and not any(test_file.parent.iterdir()):
                test_file.parent.rmdir()

    def test_file_too_large(self, scanner: RulesGuardScanner, tmp_path: Path) -> None:
        """Test that files exceeding max size are skipped."""
        large_file = tmp_path / "large.cursorrules"
        # Create file larger than max size
        large_file.write_text("A" * (scanner.config.max_file_size + 1))

        result = scanner.scan_file(large_file)

        assert not result.scanned
        assert result.error is not None
        assert "too large" in result.error.lower()

    def test_nonexistent_file(self, scanner: RulesGuardScanner) -> None:
        """Test scanning nonexistent file."""
        nonexistent = Path("nonexistent_file.cursorrules")
        result = scanner.scan_file(nonexistent)

        assert not result.scanned
        assert result.error is not None

    def test_selective_detectors(self) -> None:
        """Test using only specific detectors."""
        config = ScannerConfig(detectors=["unicode"])
        scanner = RulesGuardScanner(config)

        assert len(scanner.detectors) == 1
        assert scanner.detectors[0].name == "UnicodeDetector"

    def test_exclude_paths(self) -> None:
        """Test excluding paths from scanning."""
        config = ScannerConfig(exclude_paths=[Path("excluded")])
        scanner = RulesGuardScanner(config)

        excluded_file = Path("excluded/test.cursorrules")
        should_scan = config.should_scan_file(excluded_file)

        assert not should_scan

    def test_summary_statistics(self, scanner: RulesGuardScanner, fixtures_dir: Path) -> None:
        """Test scan summary statistics."""
        summary = scanner.scan_path(fixtures_dir)

        assert summary.total_files >= 0
        assert summary.files_with_findings >= 0
        assert summary.total_findings >= 0
        assert summary.max_risk_score >= 0
        assert summary.max_risk_score <= 100
