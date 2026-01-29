"""Pattern-based attack detection for RulesGuard.

This detector uses regex patterns to identify malicious code patterns
including code execution, remote imports, shell injection, and data exfiltration.
All patterns are compiled for performance and validated for ReDoS safety.
"""

import re
from typing import Dict, List, Pattern, Tuple
from pathlib import Path

from .base import BaseDetector
from ..models import Finding, Severity


class PatternDetector(BaseDetector):
    """Detects malicious code patterns using regex.

    Identifies:
    - Remote code loading (imports from URLs)
    - Code execution (eval, exec, compile)
    - Shell injection (os.system, subprocess with shell=True)
    - Credential theft (passwords/tokens in network calls)
    - Data exfiltration (fetch/axios to external domains)
    - File operations (suspicious file access)
    - Obfuscation (base64, hex encoding, unicode escapes)
    - Suspicious URLs (URL shorteners, unusual domains)
    """

    # CRITICAL severity patterns (25 points each)
    CRITICAL_PATTERNS: List[Tuple[str, str, str, str]] = [
        (
            r"import\s+.*(?:https?|ftp|file)://",
            "remote_import",
            "Remote import from URL detected. This can load and execute arbitrary code from external sources.",
            "Remove the remote import. Use local imports or trusted package managers only.",
        ),
        (
            r"from\s+.*(?:https?|ftp|file)://.*\s+import",
            "remote_import",
            "Remote import from URL detected. This can load and execute arbitrary code from external sources.",
            "Remove the remote import. Use local imports or trusted package managers only.",
        ),
        (
            r"__import__\s*\([^)]*(?:https?|ftp|file)://",
            "remote_import",
            "Dynamic import from URL detected. This can load and execute arbitrary code from external sources.",
            "Remove the dynamic import. Use local imports or trusted package managers only.",
        ),
        (
            r"\beval\s*\(",
            "code_execution",
            "eval() function detected. This can execute arbitrary code and is extremely dangerous.",
            "Remove eval() usage. Use safer alternatives like JSON parsing or structured data access.",
        ),
        (
            r"\bexec\s*\(",
            "code_execution",
            "exec() function detected. This can execute arbitrary code and is extremely dangerous.",
            "Remove exec() usage. Use safer alternatives like JSON parsing or structured data access.",
        ),
        (
            r"\bcompile\s*\(",
            "code_execution",
            "compile() function detected. This can compile and execute arbitrary code strings.",
            "Remove compile() usage. Prefer static code or use safer code generation methods.",
        ),
        (
            r"Function\s*\(",
            "code_execution",
            "Function() constructor detected. This can execute arbitrary code strings in JavaScript contexts.",
            "Remove Function() constructor usage. Use function declarations or arrow functions instead.",
        ),
        (
            r"os\.system\s*\(",
            "shell_injection",
            "os.system() detected. This can execute arbitrary shell commands and is dangerous.",
            "Remove os.system() usage. Use subprocess.run() with explicit arguments and shell=False.",
        ),
        (
            r"subprocess\.(?:call|run|Popen)\s*\([^)]*,?\s*shell\s*=\s*True",
            "shell_injection",
            "subprocess with shell=True detected. This can execute arbitrary shell commands and is dangerous.",
            "Remove shell=True. Use subprocess with explicit argument lists and shell=False.",
        ),
        (
            r"(?:password|token|key|secret|api_key|apiKey|apikey)\s*[=:]\s*[^,\n]*(?:fetch|post|send|request|axios)",
            "credential_theft",
            "Potential credential exfiltration detected. Passwords/tokens being sent via network calls.",
            "Remove credential exfiltration code. Never send credentials to external servers.",
        ),
        (
            r"(?:fetch|post|send|request|axios)\s*\([^)]*(?:password|token|key|secret|api_key|apiKey|apikey)",
            "credential_theft",
            "Potential credential exfiltration detected. Passwords/tokens being sent via network calls.",
            "Remove credential exfiltration code. Never send credentials to external servers.",
        ),
    ]

    # HIGH severity patterns (15 points each)
    HIGH_PATTERNS: List[Tuple[str, str, str, str]] = [
        (
            r"(?:fetch|axios|XMLHttpRequest)\s*\([^)]*https?://[^)]*\.(?:com|io|net|org|co|dev)",
            "data_exfiltration",
            "Potential data exfiltration to external domain detected.",
            "Review the network call. Ensure it's to a trusted domain and not sending sensitive data.",
        ),
        (
            r"fs\.(?:readFile|writeFile|unlink|rmdir|mkdir)\s*\(",
            "file_operation",
            "File system operation detected. This can read/write/delete files on the system.",
            "Review file operations. Ensure they're necessary and don't access sensitive system files.",
        ),
        (
            r"(?:readFile|writeFile|unlink|rmdir|mkdir)\s*\(",
            "file_operation",
            "File system operation detected. This can read/write/delete files on the system.",
            "Review file operations. Ensure they're necessary and don't access sensitive system files.",
        ),
        (
            r"(?:import|require)\s*\([^)]*http",
            "dynamic_import",
            "Dynamic import from HTTP source detected. This can load arbitrary code at runtime.",
            "Remove dynamic imports from HTTP sources. Use static imports or trusted package managers.",
        ),
    ]

    # MEDIUM severity patterns (8 points each)
    MEDIUM_PATTERNS: List[Tuple[str, str, str, str]] = [
        (
            r"base64\.(?:encode|decode|b64encode|b64decode)\s*\(",
            "obfuscation_base64",
            "Base64 encoding/decoding detected. May be used to obfuscate malicious payloads.",
            "Review base64 usage. Ensure it's for legitimate purposes (data URIs, config encoding) and not obfuscation.",
        ),
        (
            r"(?:\\x[0-9a-f]{2}|\\u[0-9a-f]{4}){5,}",
            "obfuscation_encoding",
            "Excessive hex/unicode escapes detected. May be used to obfuscate malicious code.",
            "Review encoded strings. Ensure they're for legitimate purposes and not obfuscation.",
        ),
        (
            r"(?:bit\.ly|tinyurl|t\.co|goo\.gl|short\.link|is\.gd)\/[a-zA-Z0-9]+",
            "suspicious_url",
            "URL shortener detected. May be used to hide malicious destinations.",
            "Review URL shorteners. Prefer direct URLs or trusted domains.",
        ),
    ]

    def __init__(self) -> None:
        """Initialize pattern detector with compiled regex patterns."""
        self.name_value = "PatternDetector"
        self._compiled_patterns: Dict[Severity, List[Tuple[Pattern[str], str, str, str]]] = {}

        # Compile all patterns for performance
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns for performance.

        Patterns are compiled once at initialization to avoid
        recompilation on every scan operation.
        """
        self._compiled_patterns[Severity.CRITICAL] = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), category, desc, rec)
            for pattern, category, desc, rec in self.CRITICAL_PATTERNS
        ]

        self._compiled_patterns[Severity.HIGH] = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), category, desc, rec)
            for pattern, category, desc, rec in self.HIGH_PATTERNS
        ]

        self._compiled_patterns[Severity.MEDIUM] = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), category, desc, rec)
            for pattern, category, desc, rec in self.MEDIUM_PATTERNS
        ]

    @property
    def name(self) -> str:
        """Return detector name.

        Returns:
            Detector name
        """
        return self.name_value

    def detect(self, content: str, filepath: str) -> List[Finding]:
        """Detect malicious code patterns in content.

        Args:
            content: File content to scan
            filepath: Path to the file being scanned

        Returns:
            List of Finding objects for detected patterns
        """
        self._validate_input(content, filepath)
        findings: List[Finding] = []

        # Check each severity level
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM]:
            severity_findings = self._detect_severity_patterns(
                content, filepath, severity
            )
            findings.extend(severity_findings)

        return findings

    def _detect_severity_patterns(
        self, content: str, filepath: str, severity: Severity
    ) -> List[Finding]:
        """Detect patterns for a specific severity level.

        Args:
            content: File content
            filepath: File path
            severity: Severity level to check

        Returns:
            List of findings for this severity level
        """
        findings: List[Finding] = []

        if severity not in self._compiled_patterns:
            return findings

        for pattern, category, description, recommendation in self._compiled_patterns[
            severity
        ]:
            # Find all matches
            matches = pattern.finditer(content)

            for match in matches:
                start = match.start()
                end = match.end()
                line = self._get_line_number(content, start)
                column = self._get_column_number(content, start)
                snippet = self._get_snippet(content, start, end)

                finding = Finding(
                    file_path=str(filepath),
                    line=line,
                    column=column,
                    severity=severity,
                    category=category,
                    description=description,
                    snippet=snippet,
                    recommendation=recommendation,
                    cve_ref="CVE-2026-21858",
                    detector_name=self.name,
                )
                findings.append(finding)

        return findings
