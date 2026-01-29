"""Unicode-based attack detection for RulesGuard.

This detector identifies dangerous Unicode characters that can be used
to obfuscate malicious code in configuration files. Addresses Unicode
exploits related to CVE-2026-21858.
"""

import unicodedata
from typing import Dict, List, Set, Tuple
from pathlib import Path

from .base import BaseDetector
from ..models import Finding, Severity


class UnicodeDetector(BaseDetector):
    """Detects dangerous Unicode characters in configuration files.

    Identifies:
    - Zero-width characters (ZWSP, ZWNJ, ZWJ, BOM)
    - Directional overrides (LTR/RTL embedding/override)
    - Invisible formatting characters
    - Control characters
    - Private use area characters
    - Surrogate pairs
    - BOMs in unusual positions
    """

    # Dangerous Unicode categories
    DANGEROUS_CATEGORIES: Set[str] = {
        "Cf",  # Format characters (zero-width, etc.)
        "Cc",  # Control characters
        "Cs",  # Surrogate characters
        "Co",  # Private use area
        "Cn",  # Unassigned (potential for abuse)
    }

    # Specific dangerous characters with their names and descriptions
    DANGEROUS_CHARS: Dict[str, Tuple[str, str, Severity]] = {
        "\u200B": ("ZERO WIDTH SPACE", "Invisible space that can hide code", Severity.CRITICAL),
        "\u200C": ("ZERO WIDTH NON-JOINER", "Invisible character for text shaping", Severity.CRITICAL),
        "\u200D": ("ZERO WIDTH JOINER", "Invisible character for text shaping", Severity.CRITICAL),
        "\uFEFF": ("ZERO WIDTH NO-BREAK SPACE", "BOM - should only appear at file start", Severity.CRITICAL),
        "\u202A": ("LEFT-TO-RIGHT EMBEDDING", "Directional override", Severity.HIGH),
        "\u202B": ("RIGHT-TO-LEFT EMBEDDING", "Directional override", Severity.HIGH),
        "\u202C": ("POP DIRECTIONAL FORMATTING", "Ends directional override", Severity.HIGH),
        "\u202D": ("LEFT-TO-RIGHT OVERRIDE", "Strong directional override", Severity.HIGH),
        "\u202E": ("RIGHT-TO-LEFT OVERRIDE", "Strong directional override (can reverse text)", Severity.HIGH),
        "\u2060": ("WORD JOINER", "Invisible character preventing line breaks", Severity.MEDIUM),
        "\u2061": ("FUNCTION APPLICATION", "Invisible mathematical operator", Severity.MEDIUM),
        "\u2062": ("INVISIBLE TIMES", "Invisible mathematical operator", Severity.MEDIUM),
        "\u2063": ("INVISIBLE SEPARATOR", "Invisible separator character", Severity.MEDIUM),
        "\u2064": ("INVISIBLE PLUS", "Invisible mathematical operator", Severity.MEDIUM),
        "\u2066": ("LEFT-TO-RIGHT ISOLATE", "Directional isolate", Severity.MEDIUM),
        "\u2067": ("RIGHT-TO-LEFT ISOLATE", "Directional isolate", Severity.MEDIUM),
        "\u2068": ("FIRST STRONG ISOLATE", "Directional isolate", Severity.MEDIUM),
        "\u2069": ("POP DIRECTIONAL ISOLATE", "Ends directional isolate", Severity.MEDIUM),
    }

    # BOM character (should only appear at file start)
    BOM_CHAR = "\uFEFF"

    def __init__(self) -> None:
        """Initialize Unicode detector."""
        self.name_value = "UnicodeDetector"

    @property
    def name(self) -> str:
        """Return detector name.

        Returns:
            Detector name
        """
        return self.name_value

    def detect(self, content: str, filepath: str) -> List[Finding]:
        """Detect dangerous Unicode characters in content.

        Args:
            content: File content to scan
            filepath: Path to the file being scanned

        Returns:
            List of Finding objects for detected Unicode threats
        """
        self._validate_input(content, filepath)
        findings: List[Finding] = []

        # Check for BOM in wrong position (not at start)
        bom_findings = self._detect_bom_abuse(content, filepath)
        findings.extend(bom_findings)

        # Check for specific dangerous characters
        char_findings = self._detect_dangerous_chars(content, filepath)
        findings.extend(char_findings)

        # Check for dangerous Unicode categories
        category_findings = self._detect_dangerous_categories(content, filepath)
        findings.extend(category_findings)

        return findings

    def _detect_bom_abuse(self, content: str, filepath: str) -> List[Finding]:
        """Detect BOM characters in unusual positions.

        BOM should only appear at the very start of a file. If it appears
        elsewhere, it's likely being used to obfuscate code.

        Args:
            content: File content
            filepath: File path

        Returns:
            List of findings for BOM abuse
        """
        findings: List[Finding] = []

        # Check if BOM is at start (legitimate)
        has_start_bom = content.startswith(self.BOM_CHAR)

        # Find all BOM occurrences
        position = 0
        while True:
            position = content.find(self.BOM_CHAR, position)
            if position == -1:
                break

            # If BOM is at start, it's legitimate (skip)
            if position == 0 and has_start_bom:
                position += 1
                continue

            # BOM in middle/end is suspicious
            line = self._get_line_number(content, position)
            column = self._get_column_number(content, position)
            snippet = self._get_snippet(content, position, position + 1)

            finding = Finding(
                file_path=str(filepath),
                line=line,
                column=column,
                severity=Severity.CRITICAL,
                category="unicode_bom_abuse",
                description=(
                    f"BOM (Zero Width No-Break Space, U+FEFF) found at position {position}. "
                    "BOM should only appear at file start. This may be used to obfuscate code."
                ),
                snippet=snippet,
                recommendation=(
                    "Remove the BOM character. If this is legitimate UTF-8 BOM, "
                    "it should only be at the very start of the file."
                ),
                cve_ref="CVE-2026-21858",
                detector_name=self.name,
            )
            findings.append(finding)
            position += 1

        return findings

    def _detect_dangerous_chars(self, content: str, filepath: str) -> List[Finding]:
        """Detect specific dangerous Unicode characters.

        Args:
            content: File content
            filepath: File path

        Returns:
            List of findings for dangerous characters
        """
        findings: List[Finding] = []

        for char, (char_name, description, severity) in self.DANGEROUS_CHARS.items():
            # Skip BOM here (handled separately)
            if char == self.BOM_CHAR:
                continue

            position = 0
            while True:
                position = content.find(char, position)
                if position == -1:
                    break

                line = self._get_line_number(content, position)
                column = self._get_column_number(content, position)
                snippet = self._get_snippet(content, position, position + 1)

                # Get Unicode code point
                code_point = f"U+{ord(char):04X}"

                finding = Finding(
                    file_path=str(filepath),
                    line=line,
                    column=column,
                    severity=severity,
                    category="unicode_dangerous_char",
                    description=(
                        f"{char_name} ({code_point}) detected. {description}. "
                        "This invisible character can be used to hide malicious code."
                    ),
                    snippet=snippet,
                    recommendation=(
                        f"Remove the {char_name} character. Review the surrounding code "
                        "carefully for any hidden malicious content."
                    ),
                    cve_ref="CVE-2026-21858",
                    detector_name=self.name,
                )
                findings.append(finding)
                position += 1

        return findings

    def _detect_dangerous_categories(self, content: str, filepath: str) -> List[Finding]:
        """Detect characters from dangerous Unicode categories.

        Args:
            content: File content
            filepath: File path

        Returns:
            List of findings for dangerous category characters
        """
        findings: List[Finding] = []
        seen_positions: Set[int] = set()

        for position, char in enumerate(content):
            # Skip if already reported (from specific char detection)
            if position in seen_positions:
                continue

            category = unicodedata.category(char)

            # Check if character is in dangerous category
            if category in self.DANGEROUS_CATEGORIES:
                # Skip if it's a known dangerous char (already handled)
                if char in self.DANGEROUS_CHARS:
                    continue

                # Skip common control characters that are legitimate (newlines, tabs)
                if char in {"\n", "\r", "\t"}:
                    continue

                line = self._get_line_number(content, position)
                column = self._get_column_number(content, position)
                snippet = self._get_snippet(content, position, position + 1)

                # Get character name and code point
                try:
                    char_name = unicodedata.name(char, f"UNNAMED-{ord(char):04X}")
                except ValueError:
                    char_name = f"UNNAMED-{ord(char):04X}"

                code_point = f"U+{ord(char):04X}"

                # Determine severity based on category
                severity_map = {
                    "Cf": Severity.HIGH,  # Format characters
                    "Cc": Severity.MEDIUM,  # Control characters (some are legitimate)
                    "Cs": Severity.HIGH,  # Surrogates (shouldn't appear in UTF-8)
                    "Co": Severity.MEDIUM,  # Private use (context-dependent)
                    "Cn": Severity.LOW,  # Unassigned (may be legitimate)
                }
                severity = severity_map.get(category, Severity.MEDIUM)

                finding = Finding(
                    file_path=str(filepath),
                    line=line,
                    column=column,
                    severity=severity,
                    category=f"unicode_category_{category.lower()}",
                    description=(
                        f"Character from dangerous Unicode category '{category}' detected: "
                        f"{char_name} ({code_point}). Characters in this category can be "
                        "used to obfuscate malicious code."
                    ),
                    snippet=snippet,
                    recommendation=(
                        f"Review the {char_name} character. If it's not necessary, remove it. "
                        "Ensure no malicious code is hidden using this character."
                    ),
                    cve_ref="CVE-2026-21858",
                    detector_name=self.name,
                )
                findings.append(finding)
                seen_positions.add(position)

        return findings
