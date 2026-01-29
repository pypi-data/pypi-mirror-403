"""SARIF reporter for RulesGuard.

Exports scan results in SARIF (Static Analysis Results Interchange Format)
for integration with GitHub Security, CodeQL, and other security tools.
"""

import json
from typing import Any, Dict, List
from pathlib import Path

from ..models import Finding, ScanResult, ScanSummary, Severity


class SARIFReporter:
    """SARIF reporter for scan results."""

    def __init__(self, tool_name: str = "RulesGuard", tool_version: str = "0.1.0") -> None:
        """Initialize SARIF reporter.

        Args:
            tool_name: Name of the scanning tool
            tool_version: Version of the scanning tool
        """
        self.tool_name = tool_name
        self.tool_version = tool_version

    def to_sarif(self, summary: ScanSummary) -> Dict[str, Any]:
        """Convert scan summary to SARIF format.

        Args:
            summary: Scan summary to convert

        Returns:
            SARIF format dictionary
        """
        # Collect all findings
        all_findings: List[Finding] = []
        for result in summary.results:
            all_findings.extend(result.findings)

        # Build rules (detector information)
        rules = self._build_rules(all_findings)

        # Build results (findings)
        results = [self._finding_to_sarif(f) for f in all_findings]

        return {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                            "informationUri": "https://github.com/NOTTIBOY137/RulesGuard",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ],
        }

    def _build_rules(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Build SARIF rules from findings.

        Args:
            findings: List of findings

        Returns:
            List of SARIF rule objects
        """
        # Group by category
        categories: Dict[str, Finding] = {}
        for finding in findings:
            if finding.category not in categories:
                categories[finding.category] = finding

        rules = []
        for category, example_finding in categories.items():
            rule = {
                "id": category,
                "name": category.replace("_", " ").title(),
                "shortDescription": {"text": example_finding.description},
                "helpUri": "https://github.com/NOTTIBOY137/RulesGuard",
            }

            if example_finding.cve_ref:
                rule["properties"] = {"cve": example_finding.cve_ref}

            rules.append(rule)

        return rules

    def _finding_to_sarif(self, finding: Finding) -> Dict[str, Any]:
        """Convert finding to SARIF result format.

        Args:
            finding: Finding to convert

        Returns:
            SARIF result object
        """
        severity_map = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
        }

        return {
            "ruleId": finding.category,
            "level": severity_map.get(finding.severity, "warning"),
            "message": {
                "text": finding.description,
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": str(Path(finding.file_path).as_uri()),
                        },
                        "region": {
                            "startLine": finding.line,
                            "startColumn": finding.column,
                        },
                    }
                }
            ],
            "properties": {
                "recommendation": finding.recommendation,
                "detector": finding.detector_name,
            },
        }

    def export(self, summary: ScanSummary, output_path: str) -> None:
        """Export scan summary to SARIF file.

        Args:
            summary: Scan summary to export
            output_path: Path to output SARIF file
        """
        sarif_data = self.to_sarif(summary)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sarif_data, f, indent=2, ensure_ascii=False)
