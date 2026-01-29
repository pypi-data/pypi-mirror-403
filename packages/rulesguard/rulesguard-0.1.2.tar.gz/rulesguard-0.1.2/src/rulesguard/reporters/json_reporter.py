"""JSON reporter for RulesGuard.

Exports scan results in JSON format for programmatic processing.
"""

import json
from typing import Any, Dict, List

from ..models import Finding, ScanResult, ScanSummary, Severity


class JSONReporter:
    """JSON reporter for scan results."""

    def to_dict(self, summary: ScanSummary) -> Dict[str, Any]:
        """Convert scan summary to dictionary.

        Args:
            summary: Scan summary to convert

        Returns:
            Dictionary representation of summary
        """
        return {
            "summary": {
                "total_files": summary.total_files,
                "files_with_findings": summary.files_with_findings,
                "total_findings": summary.total_findings,
                "critical_files": summary.critical_files,
                "max_risk_score": summary.max_risk_score,
            },
            "results": [self._result_to_dict(result) for result in summary.results],
        }

    def _result_to_dict(self, result: ScanResult) -> Dict[str, Any]:
        """Convert scan result to dictionary.

        Args:
            result: Scan result to convert

        Returns:
            Dictionary representation of result
        """
        return {
            "file_path": result.file_path,
            "scanned": result.scanned,
            "error": result.error,
            "risk_score": result.risk_score,
            "findings": [self._finding_to_dict(f) for f in result.findings],
        }

    def _finding_to_dict(self, finding: Finding) -> Dict[str, Any]:
        """Convert finding to dictionary.

        Args:
            finding: Finding to convert

        Returns:
            Dictionary representation of finding
        """
        return {
            "file_path": finding.file_path,
            "line": finding.line,
            "column": finding.column,
            "severity": finding.severity.value,
            "category": finding.category,
            "description": finding.description,
            "snippet": finding.snippet,
            "recommendation": finding.recommendation,
            "cve_ref": finding.cve_ref,
            "detector_name": finding.detector_name,
        }

    def export(self, summary: ScanSummary, output_path: str) -> None:
        """Export scan summary to JSON file.

        Args:
            summary: Scan summary to export
            output_path: Path to output JSON file
        """
        data = self.to_dict(summary)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
