"""Command-line interface for RulesGuard.

Provides a user-friendly CLI for scanning configuration files.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .config import ScannerConfig
from .scanner import RulesGuardScanner
from .reporters.console import ConsoleReporter
from .reporters.json_reporter import JSONReporter
from .reporters.sarif import SARIFReporter
from .models import Baseline, BaselineFinding, ScanSummary, Severity

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
        reporter = JSONReporter()
        if output:
            reporter.export(summary, str(output))
            console.print(f"[green]Results exported to {output}[/green]")
        else:
            # Print JSON to stdout
            print(json.dumps(reporter.to_dict(summary), indent=2))
    elif format.lower() == "sarif":
        reporter = SARIFReporter()
        if output:
            reporter.export(summary, str(output))
            console.print(f"[green]Results exported to {output}[/green]")
        else:
            console.print_json(json.dumps(reporter.to_sarif(summary)))
    else:
        # Console output
        reporter = ConsoleReporter()
        reporter.print_summary(summary)

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
@click.version_option(version="0.1.4", package_name="rulesguard")
def cli() -> None:
    """RulesGuard - Security scanner for AI coding assistant configuration files."""
    pass


# Main scan command (default behavior)
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
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path for JSON/SARIF export",
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
    "--recursive/--no-recursive",
    default=True,
    help="Scan directories recursively (default: True)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
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
    # Scan specific files
    rulesguard scan .cursorrules .vscode/settings.json

    \b
    # Export to JSON
    rulesguard scan . -f json -o results.json

    \b
    # Use specific detectors only
    rulesguard scan . -d unicode -d pattern

    \b
    # Fail on medium or higher severity findings
    rulesguard scan . --fail-on medium

    \b
    # Use baseline to suppress known findings
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


# Add scan to the group (as subcommand)
cli.add_command(scan, name="scan")

# For backward compatibility: make main be a function that routes to scan by default
@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
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
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path for JSON/SARIF export",
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
    "--recursive/--no-recursive",
    default=True,
    help="Scan directories recursively (default: True)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--baseline",
    type=click.Path(path_type=Path),
    help="Path to baseline file to suppress known findings",
)
@click.version_option(version="0.1.4", package_name="rulesguard")
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


if __name__ == "__main__":
    # When called as module, check if first arg is a subcommand
    if len(sys.argv) > 1 and sys.argv[1] in ["baseline", "scan"]:
        cli()
    else:
        # Backward compatibility: "rulesguard ." should work
        main()
