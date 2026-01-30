"""Module for detecting exposed secrets and credentials in code."""

import re
from typing import List, Dict, Any, Tuple

# Patterns are obfuscated or split to avoid self-detection
PATTERNS: List[Tuple[str, str, str]] = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID", "critical"),
    (
        r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]",
        "AWS Secret Access Key",
        "critical",
    ),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Token", "critical"),
    (r"AIza[0-9A-Za-z\\-_]{35}", "Google API Key", "critical"),
    (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "Private Key", "critical"),
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key", "critical"),
    (
        r"(?i)(password|passwd|secret|api_key|access_token|auth_token)\s*=\s*['\"][A-Za-z0-9_\\-]{8,128}['\"]",
        "Generic Potential Secret Assignment",
        "high",
    ),
]

IGNORED_KEYWORDS = [
    "example",
    "test",
    "change_me",
    "changeme",
    "placeholder",
    "dummy",
    "sample",
    "your_password",
    "your_secret",
    "todo",
]


class SecretScanner:
    """Dectects sensitive information using regular expressions."""

    def __init__(self):
        self.rules = [(re.compile(p), desc, sev) for p, desc, sev in PATTERNS]

    def scan(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.splitlines()
        for regex, desc, sev in self.rules:
            for match in regex.finditer(content):
                code = match.group()
                if any(k in code.lower() for k in IGNORED_KEYWORDS):
                    continue

                start = match.start()
                line_no = content.count("\n", 0, start) + 1
                if line_no <= len(lines) and any(
                    x in lines[line_no - 1] for x in ("re.compile", 'r"', "r'")
                ):
                    continue

                issues.append(
                    {
                        "pattern": desc,
                        "description": f"Potential exposed secret: {desc}",
                        "severity": sev,
                        "line": line_no,
                        "code": self._mask(code),
                    }
                )
        return issues

    def _mask(self, val: str) -> str:
        if len(val) <= 4:
            return "*" * len(val)
        return f"{val[:2]}{'*' * (len(val) - 4)}{val[-2:]}"


def detect_secrets(content: str) -> List[Dict[str, Any]]:
    """Legacy wrapper for secret detection."""
    return SecretScanner().scan(content)


def _mask_secret(secret: str) -> str:
    """Legacy internal wrapper for masking."""
    return SecretScanner()._mask(secret)
