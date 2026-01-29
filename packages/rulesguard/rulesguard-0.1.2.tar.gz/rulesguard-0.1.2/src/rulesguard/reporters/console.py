"""Rich console reporter for RulesGuard.

Provides beautiful, colorized console output using the Rich library.
"""

from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

from ..models import Finding, ScanResult, ScanSummary, Severity


class ConsoleReporter:
    """Rich console reporter for scan results."""

    def __init__(self) -> None:
        """Initialize console reporter."""
        self.console = Console()

    def print_summary(self, summary: ScanSummary) -> None:
        """Print scan summary to console.

        Args:
            summary: Scan summary to display
        """
        self.console.print("\n")

        # Summary panel
        summary_text = f"""
[bold]Files Scanned:[/bold] {summary.total_files}
[bold]Files with Findings:[/bold] {summary.files_with_findings}
[bold]Total Findings:[/bold] {summary.total_findings}
[bold]Critical Files:[/bold] {summary.critical_files}
[bold]Max Risk Score:[/bold] {summary.max_risk_score}/100
        """

        if summary.max_risk_score >= 50:
            color = "red"
        elif summary.max_risk_score >= 25:
            color = "yellow"
        else:
            color = "green"

        self.console.print(
            Panel(summary_text.strip(), title="[bold]Scan Summary[/bold]", border_style=color)
        )

        # Findings table
        if summary.total_findings > 0:
            self._print_findings_table(summary.results)

    def _print_findings_table(self, results: List[ScanResult]) -> None:
        """Print findings in a table format.

        Args:
            results: List of scan results
        """
        table = Table(title="[bold]Security Findings[/bold]", show_header=True, header_style="bold")

        table.add_column("File", style="cyan", no_wrap=False)
        table.add_column("Line", justify="right", style="magenta")
        table.add_column("Severity", style="bold")
        table.add_column("Category", style="blue")
        table.add_column("Description", style="white")

        for result in results:
            if not result.findings:
                continue

            for finding in result.findings:
                severity_color = self._get_severity_color(finding.severity)
                severity_text = Text(finding.severity.value, style=severity_color)

                table.add_row(
                    finding.file_path,
                    str(finding.line),
                    severity_text,
                    finding.category,
                    finding.description[:80] + "..." if len(finding.description) > 80 else finding.description,
                )

        self.console.print("\n")
        self.console.print(table)

    def print_finding_details(self, finding: Finding) -> None:
        """Print detailed information about a finding.

        Args:
            finding: Finding to display
        """
        severity_color = self._get_severity_color(finding.severity)

        details = f"""
[bold]File:[/bold] {finding.file_path}
[bold]Location:[/bold] Line {finding.line}, Column {finding.column}
[bold]Severity:[/bold] [{severity_color}]{finding.severity.value}[/{severity_color}]
[bold]Category:[/bold] {finding.category}
[bold]Detector:[/bold] {finding.detector_name}
[bold]Description:[/bold] {finding.description}
[bold]Recommendation:[/bold] {finding.recommendation}
        """

        if finding.cve_ref:
            details += f"\n[bold]CVE Reference:[/bold] {finding.cve_ref}"

        self.console.print(Panel(details.strip(), title="[bold]Finding Details[/bold]"))

        # Code snippet
        if finding.snippet:
            syntax = Syntax(
                finding.snippet,
                "python",
                theme="monokai",
                line_numbers=True,
                start_line=max(1, finding.line - 2),
            )
            self.console.print("\n[bold]Code Snippet:[/bold]")
            self.console.print(syntax)

    def _get_severity_color(self, severity: Severity) -> str:
        """Get color for severity level.

        Args:
            severity: Severity level

        Returns:
            Color name for Rich styling
        """
        color_map = {
            Severity.CRITICAL: "bold red",
            Severity.HIGH: "red",
            Severity.MEDIUM: "yellow",
            Severity.LOW: "blue",
        }
        return color_map.get(severity, "white")
