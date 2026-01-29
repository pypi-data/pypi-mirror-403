"""Command-line interface for RulesGuard.

Provides a user-friendly CLI for scanning configuration files.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .config import ScannerConfig
from .scanner import RulesGuardScanner
from .reporters.console import ConsoleReporter
from .reporters.json_reporter import JSONReporter
from .reporters.sarif import SARIFReporter
from .models import ScanSummary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

console = Console()


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
@click.version_option(version="0.1.1")
def main(
    paths: tuple,
    exclude: tuple,
    detector: tuple,
    max_size: int,
    output: Optional[Path],
    format: str,
    recursive: bool,
    verbose: bool,
) -> None:
    """RulesGuard - Security scanner for AI coding assistant configuration files.

    Scans .cursorrules, .vscode/settings.json, and similar files for
    malicious code patterns. Addresses CVE-2026-21858 "Rules File Backdoor".

    Examples:

    \b
    # Scan current directory
    rulesguard .

    \b
    # Scan specific files
    rulesguard .cursorrules .vscode/settings.json

    \b
    # Export to JSON
    rulesguard . -f json -o results.json

    \b
    # Use specific detectors only
    rulesguard . -d unicode -d pattern
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

        # Exit with error code if findings detected
        if summary.total_findings > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
