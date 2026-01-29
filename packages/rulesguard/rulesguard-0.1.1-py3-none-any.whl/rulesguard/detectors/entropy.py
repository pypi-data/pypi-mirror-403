"""Entropy-based detection for encoded/obfuscated content.

This detector identifies high-entropy strings that may indicate
base64-encoded payloads, hex-encoded data, or other obfuscation techniques.
"""

import base64
import re
from typing import List
from pathlib import Path

from .base import BaseDetector
from ..models import Finding, Severity


class EntropyDetector(BaseDetector):
    """Detects high-entropy encoded content.

    Identifies:
    - Base64-encoded strings (potential payloads)
    - Hex-encoded strings (potential obfuscation)
    - High-entropy strings (random-looking data)
    """

    # Base64 pattern (alphanumeric + / + = padding)
    # Matches base64 strings (works inside or outside quotes)
    # Minimum 16 chars total (including padding) to catch shorter payloads
    BASE64_PATTERN = re.compile(
        r"[A-Za-z0-9+/]{14,}(?:==|=)?|[A-Za-z0-9+/]{16,}"
    )

    # Hex pattern (long sequences of hex characters)
    HEX_PATTERN = re.compile(r"(?:[0-9a-fA-F]{2}){20,}")

    # Minimum length for suspicious encoded content (reduced to catch shorter payloads)
    MIN_ENCODED_LENGTH = 16

    def __init__(self) -> None:
        """Initialize entropy detector."""
        self.name_value = "EntropyDetector"

    @property
    def name(self) -> str:
        """Return detector name.

        Returns:
            Detector name
        """
        return self.name_value

    def detect(self, content: str, filepath: str) -> List[Finding]:
        """Detect high-entropy encoded content.

        Args:
            content: File content to scan
            filepath: Path to the file being scanned

        Returns:
            List of Finding objects for detected encoded content
        """
        self._validate_input(content, filepath)
        findings: List[Finding] = []

        # Check for base64-encoded content
        base64_findings = self._detect_base64(content, filepath)
        findings.extend(base64_findings)

        # Check for hex-encoded content
        hex_findings = self._detect_hex(content, filepath)
        findings.extend(hex_findings)

        return findings

    def _detect_base64(self, content: str, filepath: str) -> List[Finding]:
        """Detect base64-encoded strings.

        Args:
            content: File content
            filepath: File path

        Returns:
            List of findings for base64 content
        """
        findings: List[Finding] = []

        for match in self.BASE64_PATTERN.finditer(content):
            encoded_str = match.group(0)
            
            # Skip if too short
            if len(encoded_str) < self.MIN_ENCODED_LENGTH:
                continue

            # Try to decode to verify it's valid base64
            try:
                decoded = base64.b64decode(encoded_str, validate=True)
                # Flag long base64 strings (>=32 chars) regardless of content,
                # or shorter ones if they decode to mostly non-printable
                if len(decoded) > 0:
                    printable_ratio = sum(
                        1 for b in decoded if 32 <= b <= 126 or b in {9, 10, 13}
                    ) / len(decoded)

                    # Flag if: long string (>=32 chars) OR mostly non-printable
                    should_flag = len(encoded_str) >= 32 or printable_ratio < 0.7
                    if should_flag:
                        start = match.start()
                        end = match.end()
                        line = self._get_line_number(content, start)
                        column = self._get_column_number(content, start)
                        snippet = self._get_snippet(content, start, end)

                        finding = Finding(
                            file_path=str(filepath),
                            line=line,
                            column=column,
                            severity=Severity.MEDIUM,
                            category="encoded_base64",
                            description=(
                                f"Long base64-encoded string detected ({len(encoded_str)} chars). "
                                "This may be an obfuscated payload. Decoded content contains "
                                "non-printable characters."
                            ),
                            snippet=snippet,
                            recommendation=(
                                "Review the base64-encoded content. If it's not for legitimate "
                                "purposes (data URIs, config encoding), it may be obfuscated code. "
                                "Decode and inspect the content."
                            ),
                            cve_ref="CVE-2026-21858",
                            detector_name=self.name,
                        )
                        findings.append(finding)
            except Exception:
                # Invalid base64, skip
                continue

        return findings

    def _detect_hex(self, content: str, filepath: str) -> List[Finding]:
        """Detect hex-encoded strings.

        Args:
            content: File content
            filepath: File path

        Returns:
            List of findings for hex content
        """
        findings: List[Finding] = []

        for match in self.HEX_PATTERN.finditer(content):
            hex_str = match.group(0)

            # Skip if too short
            if len(hex_str) < self.MIN_ENCODED_LENGTH:
                continue

            start = match.start()
            end = match.end()
            line = self._get_line_number(content, start)
            column = self._get_column_number(content, start)
            snippet = self._get_snippet(content, start, end)

            finding = Finding(
                file_path=str(filepath),
                line=line,
                column=column,
                severity=Severity.LOW,
                category="encoded_hex",
                description=(
                    f"Long hex-encoded string detected ({len(hex_str)} chars). "
                    "This may be used to obfuscate code or data."
                ),
                snippet=snippet,
                recommendation=(
                    "Review the hex-encoded content. If it's not for legitimate purposes, "
                    "it may be obfuscated code. Decode and inspect the content."
                ),
                cve_ref="CVE-2026-21858",
                detector_name=self.name,
            )
            findings.append(finding)

        return findings
