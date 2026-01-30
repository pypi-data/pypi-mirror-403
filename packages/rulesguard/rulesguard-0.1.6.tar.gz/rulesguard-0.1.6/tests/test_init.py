"""Test module for init command.

Tests cover:
- Audit mode workflow generation (no failure step)
- Gate mode workflow generation (with failure step)
- Baseline injection in workflows
- Template selection based on mode
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestInitCommand:
    """Test suite for init command."""

    def test_init_audit_mode_workflow(self, tmp_path: Path) -> None:
        """Test that init writes audit-mode workflow without failure step."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Run init with audit mode (default)
            result = subprocess.run(
                [sys.executable, "-m", "rulesguard.cli", "init", "--mode", "audit"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Check workflow file was created
            workflow_file = tmp_path / ".github" / "workflows" / "rulesguard.yml"
            assert workflow_file.exists(), "Workflow file should be created"

            # Read workflow content
            workflow_content = workflow_file.read_text(encoding="utf-8")

            # Check that it's using the audit template (no failure step)
            # Should NOT have "Fail job" step
            assert "Fail job" not in workflow_content, "Audit mode should not have failure step"

            # Should have upload SARIF step
            assert "Upload SARIF" in workflow_content, "Should have SARIF upload step"

            # Check action version
            assert "@v0.1.6" in workflow_content, "Should use v0.1.6"

        finally:
            os.chdir(original_cwd)

    def test_init_gate_mode_workflow(self, tmp_path: Path) -> None:
        """Test that init writes gate-mode workflow with failure step."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Run init with gate mode
            result = subprocess.run(
                [sys.executable, "-m", "rulesguard.cli", "init", "--mode", "gate", "--fail-on", "critical"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Check workflow file was created
            workflow_file = tmp_path / ".github" / "workflows" / "rulesguard.yml"
            assert workflow_file.exists(), "Workflow file should be created"

            # Read workflow content
            workflow_content = workflow_file.read_text(encoding="utf-8")

            # Check that it's using the gate template (with failure step)
            # Should have "Fail job" step
            assert "Fail job" in workflow_content, "Gate mode should have failure step"

            # Check failure step condition
            assert "steps.scan.outputs.exit_code != '0'" in workflow_content, "Failure step should check exit_code"

            # Should have upload SARIF step
            assert "Upload SARIF" in workflow_content, "Should have SARIF upload step"

            # Check action version
            assert "@v0.1.6" in workflow_content, "Should use v0.1.6"

            # Check fail_on value
            assert "fail_on: critical" in workflow_content, "Should use specified fail_on value"

        finally:
            os.chdir(original_cwd)

    def test_init_baseline_injection(self, tmp_path: Path) -> None:
        """Test that --with-baseline injects baseline usage in workflow."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Run init with baseline flag
            result = subprocess.run(
                [sys.executable, "-m", "rulesguard.cli", "init", "--mode", "audit", "--with-baseline"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Check workflow file was created
            workflow_file = tmp_path / ".github" / "workflows" / "rulesguard.yml"
            assert workflow_file.exists(), "Workflow file should be created"

            # Read workflow content
            workflow_content = workflow_file.read_text(encoding="utf-8")

            # Check that baseline is included in action inputs
            assert "baseline: .rulesguard.baseline.json" in workflow_content, "Should include baseline in action inputs"

        finally:
            os.chdir(original_cwd)

    def test_init_default_mode_is_audit(self, tmp_path: Path) -> None:
        """Test that default mode is audit (no failure step)."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Run init without specifying mode (should default to audit)
            result = subprocess.run(
                [sys.executable, "-m", "rulesguard.cli", "init"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Check workflow file was created
            workflow_file = tmp_path / ".github" / "workflows" / "rulesguard.yml"
            assert workflow_file.exists(), "Workflow file should be created"

            # Read workflow content
            workflow_content = workflow_file.read_text(encoding="utf-8")

            # Check that it's audit mode (no failure step)
            # Should NOT have "Fail job" step
            assert "Fail job" not in workflow_content, "Default mode should be audit (no failure step)"

        finally:
            os.chdir(original_cwd)

    def test_init_fail_on_parameter(self, tmp_path: Path) -> None:
        """Test that --fail-on parameter is correctly set in workflow."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Run init with custom fail-on value
            result = subprocess.run(
                [sys.executable, "-m", "rulesguard.cli", "init", "--mode", "gate", "--fail-on", "high"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"

            # Check workflow file was created
            workflow_file = tmp_path / ".github" / "workflows" / "rulesguard.yml"
            assert workflow_file.exists(), "Workflow file should be created"

            # Read workflow content
            workflow_content = workflow_file.read_text(encoding="utf-8")

            # Check fail_on value
            assert "fail_on: high" in workflow_content, "Should use specified fail_on value"

        finally:
            os.chdir(original_cwd)
