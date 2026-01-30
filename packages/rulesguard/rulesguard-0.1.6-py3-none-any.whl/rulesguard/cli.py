"""Command-line interface for RulesGuard.

Provides a user-friendly CLI for scanning configuration files.
"""

import json
import logging
import sys
from importlib import resources
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .config import ScannerConfig
from .models import Baseline, BaselineFinding, Severity
from .reporters.console import ConsoleReporter
from .reporters.json_reporter import JSONReporter
from .reporters.sarif import SARIFReporter
from .scanner import RulesGuardScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

console = Console()


def _severity_meets_threshold(severity: Severity, threshold: Severity) -> bool:
    """Check if a severity meets or exceeds the threshold.

    Args:
        severity: The severity level to check
        threshold: The minimum severity threshold

    Returns:
        True if severity meets or exceeds threshold, False otherwise
    """
    severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    severity_index = severity_order.index(severity)
    threshold_index = severity_order.index(threshold)
    return severity_index >= threshold_index


def _run_scan(
    paths: tuple,
    exclude: tuple,
    detector: tuple,
    max_size: int,
    output: Optional[Path],
    format: str,
    fail_on: str,
    recursive: bool,
    verbose: bool,
    baseline: Optional[Path],
) -> None:
    """Run the scan operation.

    Args:
        paths: Paths to scan
        exclude: Paths to exclude
        detector: Detectors to enable
        max_size: Maximum file size
        output: Output file path
        format: Output format
        fail_on: Fail threshold
        recursive: Whether to scan recursively
        verbose: Enable verbose logging
        baseline: Baseline file path
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate paths
    if not paths:
        click.echo("Error: No paths specified", err=True)
        sys.exit(1)

    # Build configuration
    config = ScannerConfig(
        target_paths=list(paths),
        detectors=list(detector) if detector else [],
        exclude_paths=list(exclude),
        max_file_size=max_size,
        recursive=recursive,
        baseline_path=baseline,
    )

    # Initialize scanner
    scanner = RulesGuardScanner(config)

    # Run scan
    console.print("[bold blue]Scanning files...[/bold blue]")
    summary = scanner.scan()

    # Report results
    if format.lower() == "json":
        json_reporter = JSONReporter()
        if output:
            json_reporter.export(summary, str(output))
            console.print(f"[green]Results exported to {output}[/green]")
        else:
            # Print JSON to stdout
            print(json.dumps(json_reporter.to_dict(summary), indent=2))
    elif format.lower() == "sarif":
        sarif_reporter = SARIFReporter()
        if output:
            sarif_reporter.export(summary, str(output))
            console.print(f"[green]Results exported to {output}[/green]")
        else:
            console.print_json(json.dumps(sarif_reporter.to_sarif(summary)))
    else:
        # Console output
        console_reporter = ConsoleReporter()
        console_reporter.print_summary(summary)

    # Check if we should exit with error code based on --fail-on threshold
    if fail_on.lower() != "none":
        severity_order = {
            "low": Severity.LOW,
            "medium": Severity.MEDIUM,
            "high": Severity.HIGH,
            "critical": Severity.CRITICAL,
        }
        threshold = severity_order.get(fail_on.lower())

        if threshold:
            # Check if any findings meet or exceed the threshold
            for result in summary.results:
                for finding in result.findings:
                    if _severity_meets_threshold(finding.severity, threshold):
                        sys.exit(1)


# Create the group
@click.group()
@click.version_option(version="0.1.6", package_name="rulesguard")
def cli() -> None:
    """RulesGuard - Security scanner for AI coding assistant configuration files."""
    pass


# Main scan command (for subcommand usage: "rulesguard scan .")
@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    type=click.Path(path_type=Path),
    help="Paths to exclude from scanning",
)
@click.option(
    "--detector",
    "-d",
    multiple=True,
    help="Detectors to enable (unicode, pattern, entropy). Default: all",
)
@click.option(
    "--max-size",
    type=int,
    default=10 * 1024 * 1024,
    help="Maximum file size to scan in bytes (default: 10MB)",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path for JSON/SARIF export"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["console", "json", "sarif"], case_sensitive=False),
    default="console",
    help="Output format (default: console)",
)
@click.option(
    "--fail-on",
    type=click.Choice(["none", "low", "medium", "high", "critical"], case_sensitive=False),
    default="critical",
    help="Exit with non-zero code if findings >= LEVEL (default: critical)",
)
@click.option(
    "--recursive/--no-recursive", default=True, help="Scan directories recursively (default: True)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--baseline",
    type=click.Path(path_type=Path),
    help="Path to baseline file to suppress known findings",
)
def scan(
    paths: tuple,
    exclude: tuple,
    detector: tuple,
    max_size: int,
    output: Optional[Path],
    format: str,
    fail_on: str,
    recursive: bool,
    verbose: bool,
    baseline: Optional[Path],
) -> None:
    """Scan files for security threats.

    Scans .cursorrules, .vscode/settings.json, and similar files for
    malicious code patterns and policy violations.

    Examples:

    \b
    # Scan current directory
    rulesguard scan .

    \b
    # Scan with baseline
    rulesguard scan . --baseline .rulesguard.baseline.json
    """
    _run_scan(
        paths=paths,
        exclude=exclude,
        detector=detector,
        max_size=max_size,
        output=output,
        format=format,
        fail_on=fail_on,
        recursive=recursive,
        verbose=verbose,
        baseline=baseline,
    )


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["audit", "gate"], case_sensitive=False),
    default="audit",
    help="Workflow mode: audit (never fails) or gate (fails on findings) (default: audit)",
)
@click.option(
    "--fail-on",
    type=click.Choice(["none", "low", "medium", "high", "critical"], case_sensitive=False),
    default="critical",
    help="Fail threshold for gate mode (default: critical)",
)
@click.option(
    "--with-baseline",
    is_flag=True,
    help="Generate baseline file from current scan and include in workflow",
)
@click.option("--with-pre-commit", is_flag=True, help="Generate .pre-commit-config.yaml")
def init(mode: str, fail_on: str, with_baseline: bool, with_pre_commit: bool) -> None:
    """Initialize RulesGuard in your repository.

    Generates:
    - .github/workflows/rulesguard.yml (GitHub Actions workflow)
    - .rulesguardignore (ignore patterns)
    - .rulesguard.baseline.json (optional, if --with-baseline)
    - .pre-commit-config.yaml (optional, if --with-pre-commit)

    Examples:

    \b
    # Basic setup (audit mode - never fails)
    rulesguard init

    \b
    # Gate mode (fails on findings)
    rulesguard init --mode gate --fail-on critical

    \b
    # With baseline generation
    rulesguard init --with-baseline

    \b
    # With pre-commit hook
    rulesguard init --with-pre-commit
    """
    repo_root = Path.cwd()

    # Load templates from package
    try:
        # Python 3.9+ compatible resource access
        templates_pkg = resources.files("rulesguard.templates")

        # Select template based on mode
        if mode.lower() == "gate":
            workflow_template_name = "rulesguard-gate.yml"
        else:
            workflow_template_name = "rulesguard-audit.yml"

        workflow_template = templates_pkg / workflow_template_name
        ignore_template = templates_pkg / "rulesguardignore"

        workflow_content = workflow_template.read_text(encoding="utf-8")
        ignore_content = ignore_template.read_text(encoding="utf-8")
    except (AttributeError, FileNotFoundError):
        # Fallback for older Python or if templates not found
        console.print("[red]Error: Could not load templates from package[/red]")
        return

    # Replace placeholders in workflow template
    # Only use fail_on in gate mode (audit mode ignores it but we still set it)
    workflow_content = workflow_content.replace("{FAIL_ON}", fail_on.lower())

    # Handle baseline injection
    baseline_line = ""
    if with_baseline:
        baseline_line = "\n          baseline: .rulesguard.baseline.json"
    workflow_content = workflow_content.replace("{BASELINE}", baseline_line)

    # Create .github/workflows directory if needed
    workflows_dir = repo_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Generate GitHub Actions workflow
    workflow_file = workflows_dir / "rulesguard.yml"
    if not workflow_file.exists():
        workflow_file.write_text(workflow_content, encoding="utf-8")
        console.print(f"[green]Created {workflow_file}[/green]")
    else:
        console.print(f"[yellow]{workflow_file} already exists, skipping[/yellow]")

    # Generate .rulesguardignore
    ignore_file = repo_root / ".rulesguardignore"
    if not ignore_file.exists():
        ignore_file.write_text(ignore_content, encoding="utf-8")
        console.print(f"[green]Created {ignore_file}[/green]")
    else:
        console.print(f"[yellow]{ignore_file} already exists, skipping[/yellow]")

    # Generate baseline if requested
    if with_baseline:
        baseline_file = repo_root / ".rulesguard.baseline.json"
        console.print("[bold blue]Generating baseline from current scan...[/bold blue]")

        config = ScannerConfig(
            target_paths=[repo_root],
            recursive=True,
        )
        scanner = RulesGuardScanner(config)
        summary = scanner.scan()

        baseline_obj = Baseline()
        for result in summary.results:
            for finding in result.findings:
                baseline_finding = BaselineFinding.from_finding(finding, repo_root)
                baseline_obj.add_finding(baseline_finding)

        baseline_obj.save(baseline_file)
        console.print(
            f"[green]Created {baseline_file} with {len(baseline_obj.findings)} findings[/green]"
        )

    # Generate pre-commit config if requested
    if with_pre_commit:
        precommit_file = repo_root / ".pre-commit-config.yaml"
        if not precommit_file.exists():
            precommit_content = """repos:
  - repo: https://github.com/NOTTIBOY137/RulesGuard
    rev: v0.1.5
    hooks:
      - id: rulesguard
        name: RulesGuard Security Scan
        entry: rulesguard
        language: python
        args: [".", "--fail-on", "critical"]
"""
            precommit_file.write_text(precommit_content)
            console.print(f"[green]Created {precommit_file}[/green]")
        else:
            console.print(f"[yellow]{precommit_file} already exists, skipping[/yellow]")

    console.print("\n[bold green]RulesGuard initialized![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Review and customize .rulesguardignore")
    if with_baseline:
        console.print("  2. Review .rulesguard.baseline.json and commit if acceptable")
    console.print("  3. Commit the generated files to your repository")
    if with_pre_commit:
        console.print("  4. Install pre-commit: pre-commit install")


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=".rulesguard.baseline.json",
    help="Output path for baseline file (default: .rulesguard.baseline.json)",
)
@click.option(
    "--detector",
    "-d",
    multiple=True,
    help="Detectors to enable (unicode, pattern, entropy). Default: all",
)
@click.option(
    "--max-size",
    type=int,
    default=10 * 1024 * 1024,
    help="Maximum file size to scan in bytes (default: 10MB)",
)
def baseline(path: Path, output: Path, detector: tuple, max_size: int) -> None:
    """Generate a baseline file from current scan results.

    The baseline captures known findings so they can be suppressed in future scans.
    This is useful for CI/CD where you want to only fail on new findings.

    Examples:

    \b
    # Generate baseline from current directory
    rulesguard baseline . -o .rulesguard.baseline.json

    \b
    # Use baseline in subsequent scans
    rulesguard scan . --baseline .rulesguard.baseline.json
    """
    # Build configuration
    config = ScannerConfig(
        target_paths=[path],
        detectors=list(detector) if detector else [],
        max_file_size=max_size,
        recursive=True,
    )

    # Initialize scanner
    scanner = RulesGuardScanner(config)

    # Run scan
    console.print("[bold blue]Scanning files to generate baseline...[/bold blue]")
    summary = scanner.scan()

    # Create baseline from all findings
    baseline_obj = Baseline()
    baseline_root = path if path.is_dir() else path.parent

    for result in summary.results:
        for finding in result.findings:
            baseline_finding = BaselineFinding.from_finding(finding, baseline_root)
            baseline_obj.add_finding(baseline_finding)

    # Save baseline
    baseline_obj.save(output)
    console.print(f"[green]Baseline saved to {output}[/green]")
    console.print(f"[dim]Found {len(baseline_obj.findings)} findings in baseline[/dim]")


# Backward compatibility: main command for "rulesguard ." usage
@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    type=click.Path(path_type=Path),
    help="Paths to exclude from scanning",
)
@click.option(
    "--detector",
    "-d",
    multiple=True,
    help="Detectors to enable (unicode, pattern, entropy). Default: all",
)
@click.option(
    "--max-size",
    type=int,
    default=10 * 1024 * 1024,
    help="Maximum file size to scan in bytes (default: 10MB)",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path for JSON/SARIF export"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["console", "json", "sarif"], case_sensitive=False),
    default="console",
    help="Output format (default: console)",
)
@click.option(
    "--fail-on",
    type=click.Choice(["none", "low", "medium", "high", "critical"], case_sensitive=False),
    default="critical",
    help="Exit with non-zero code if findings >= LEVEL (default: critical)",
)
@click.option(
    "--recursive/--no-recursive", default=True, help="Scan directories recursively (default: True)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--baseline",
    type=click.Path(path_type=Path),
    help="Path to baseline file to suppress known findings",
)
@click.version_option(version="0.1.6", package_name="rulesguard")
def main(
    paths: tuple,
    exclude: tuple,
    detector: tuple,
    max_size: int,
    output: Optional[Path],
    format: str,
    fail_on: str,
    recursive: bool,
    verbose: bool,
    baseline: Optional[Path],
) -> None:
    """RulesGuard - Security scanner for AI coding assistant configuration files.

    Scans .cursorrules, .vscode/settings.json, and similar files for
    malicious code patterns and policy violations.

    Examples:

    \b
    # Scan current directory
    rulesguard .

    \b
    # Scan with baseline
    rulesguard . --baseline .rulesguard.baseline.json

    \b
    # Generate baseline
    rulesguard baseline . -o .rulesguard.baseline.json

    \b
    # Initialize RulesGuard
    rulesguard init
    """
    _run_scan(
        paths=paths,
        exclude=exclude,
        detector=detector,
        max_size=max_size,
        output=output,
        format=format,
        fail_on=fail_on,
        recursive=recursive,
        verbose=verbose,
        baseline=baseline,
    )


# Entry point router
def _entry_point() -> None:
    """Route to group for subcommands or main for backward compatibility."""
    if len(sys.argv) > 1 and sys.argv[1] in ["baseline", "scan", "init"]:
        cli()
    else:
        main()


if __name__ == "__main__":
    _entry_point()
