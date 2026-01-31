"""Secret detection for PairCoder.

This module provides:
- SecretScanner: Scans files and diffs for leaked credentials
- SecretMatch: Data class for detected secrets
- AllowlistConfig: Configuration for false positive suppression
"""

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class SecretType(Enum):
    """Types of secrets that can be detected."""
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    GITHUB_PAT = "github_pat"
    GITHUB_OAUTH = "github_oauth"
    SLACK_TOKEN = "slack_token"
    SLACK_WEBHOOK = "slack_webhook"
    PRIVATE_KEY = "private_key"
    SSH_PRIVATE_KEY = "ssh_private_key"
    JWT_TOKEN = "jwt_token"
    GENERIC_API_KEY = "generic_api_key"
    GENERIC_PASSWORD = "generic_password"
    GENERIC_SECRET = "generic_secret"
    GENERIC_TOKEN = "generic_token"
    DATABASE_URL = "database_url"
    STRIPE_KEY = "stripe_key"
    SENDGRID_KEY = "sendgrid_key"
    TWILIO_KEY = "twilio_key"
    GOOGLE_API_KEY = "google_api_key"


@dataclass
class SecretMatch:
    """A detected secret in code.

    Attributes:
        secret_type: The type of secret detected
        file_path: Path to the file containing the secret
        line_number: Line number where secret was found
        line_content: The line containing the secret (redacted)
        match: The matched pattern (redacted for display)
        confidence: Confidence score (0-1) for the detection
    """
    secret_type: SecretType
    file_path: str
    line_number: int
    line_content: str
    match: str
    confidence: float = 1.0

    def __post_init__(self):
        """Redact sensitive content after initialization."""
        # Redact the actual secret value for safe display
        self.match_redacted = self._redact(self.match)
        self.line_redacted = self._redact_line(self.line_content, self.match)

    def _redact(self, value: str) -> str:
        """Redact a secret value for safe display."""
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    def _redact_line(self, line: str, match: str) -> str:
        """Redact the secret in the line content."""
        return line.replace(match, self._redact(match))

    def format(self) -> str:
        """Format the match for display."""
        return (
            f"{self.file_path}:{self.line_number}: "
            f"[{self.secret_type.value}] {self.line_redacted.strip()}"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "type": self.secret_type.value,
            "file": self.file_path,
            "line": self.line_number,
            "content": self.line_redacted,
            "confidence": self.confidence,
        }


@dataclass
class AllowlistConfig:
    """Configuration for secret detection allowlist.

    Attributes:
        allowed_patterns: Patterns that are allowed (e.g., example keys)
        allowed_files: File patterns to skip scanning
        allowed_hashes: SHA256 hashes of allowed secret values
    """
    allowed_patterns: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    allowed_hashes: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "AllowlistConfig":
        """Load allowlist configuration from YAML file.

        Args:
            path: Path to the allowlist YAML file

        Returns:
            AllowlistConfig instance
        """
        if not path.exists():
            return cls()

        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return cls(
            allowed_patterns=data.get("allowed_patterns", []),
            allowed_files=data.get("allowed_files", []),
            allowed_hashes=data.get("allowed_hashes", []),
        )

    def is_allowed_file(self, file_path: str) -> bool:
        """Check if a file should be skipped.

        Args:
            file_path: Path to check

        Returns:
            True if the file should be skipped
        """
        import fnmatch
        for pattern in self.allowed_files:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def is_allowed_pattern(self, match: str) -> bool:
        """Check if a matched value is in the allowlist.

        Args:
            match: The matched secret value

        Returns:
            True if the match is allowed
        """
        import fnmatch
        for pattern in self.allowed_patterns:
            if fnmatch.fnmatch(match, pattern):
                return True
        return False


# Secret detection patterns with confidence scores
SECRET_PATTERNS: list[tuple[str, SecretType, float]] = [
    # AWS Credentials
    (r'AKIA[0-9A-Z]{16}', SecretType.AWS_ACCESS_KEY, 1.0),
    (r'(?i)aws_secret_access_key\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', SecretType.AWS_SECRET_KEY, 0.95),
    (r'(?i)AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', SecretType.AWS_SECRET_KEY, 0.95),

    # GitHub Tokens
    (r'ghp_[A-Za-z0-9]{36}', SecretType.GITHUB_TOKEN, 1.0),
    (r'github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}', SecretType.GITHUB_PAT, 1.0),
    (r'gho_[A-Za-z0-9]{36}', SecretType.GITHUB_OAUTH, 1.0),
    (r'ghs_[A-Za-z0-9]{36}', SecretType.GITHUB_TOKEN, 1.0),
    (r'ghr_[A-Za-z0-9]{36}', SecretType.GITHUB_TOKEN, 1.0),

    # Slack Tokens
    (r'xox[baprs]-[A-Za-z0-9-]{10,}', SecretType.SLACK_TOKEN, 1.0),
    (r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+', SecretType.SLACK_WEBHOOK, 1.0),

    # Private Keys - use non-capturing groups to ensure full header is matched
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', SecretType.PRIVATE_KEY, 1.0),
    (r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----', SecretType.SSH_PRIVATE_KEY, 1.0),
    (r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----', SecretType.PRIVATE_KEY, 1.0),
    (r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----', SecretType.PRIVATE_KEY, 1.0),
    (r'-----BEGIN\s+PGP\s+PRIVATE\s+KEY\s+BLOCK-----', SecretType.PRIVATE_KEY, 1.0),

    # JWT Tokens
    (r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', SecretType.JWT_TOKEN, 0.9),

    # Database URLs with credentials
    (r'(?i)(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@[^/]+', SecretType.DATABASE_URL, 0.95),

    # Stripe Keys
    (r'sk_live_[A-Za-z0-9]{24,}', SecretType.STRIPE_KEY, 1.0),
    (r'sk_test_[A-Za-z0-9]{24,}', SecretType.STRIPE_KEY, 0.8),
    (r'pk_live_[A-Za-z0-9]{24,}', SecretType.STRIPE_KEY, 0.9),

    # SendGrid
    (r'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}', SecretType.SENDGRID_KEY, 1.0),

    # Twilio
    (r'SK[A-Za-z0-9]{32}', SecretType.TWILIO_KEY, 0.85),

    # Google API Keys
    (r'AIza[A-Za-z0-9_-]{35}', SecretType.GOOGLE_API_KEY, 1.0),

    # Generic patterns (lower confidence)
    (r'(?i)api[_-]?key\s*[=:]\s*["\']([^"\']{16,})["\']', SecretType.GENERIC_API_KEY, 0.7),
    (r'(?i)apikey\s*[=:]\s*["\']([^"\']{16,})["\']', SecretType.GENERIC_API_KEY, 0.7),
    (r'(?i)password\s*[=:]\s*["\']([^"\']{8,})["\']', SecretType.GENERIC_PASSWORD, 0.6),
    (r'(?i)passwd\s*[=:]\s*["\']([^"\']{8,})["\']', SecretType.GENERIC_PASSWORD, 0.6),
    (r'(?i)secret\s*[=:]\s*["\']([^"\']{8,})["\']', SecretType.GENERIC_SECRET, 0.6),
    (r'(?i)token\s*[=:]\s*["\']([^"\']{20,})["\']', SecretType.GENERIC_TOKEN, 0.6),
]

# Patterns to ignore (false positives)
IGNORE_PATTERNS: list[str] = [
    r'os\.environ\.get\s*\(["\']',  # Reading from env vars
    r'os\.getenv\s*\(["\']',  # Reading from env vars
    r'environ\[["\']',  # Accessing environ dict
    r'#.*password',  # Comments about passwords
    r'#.*secret',  # Comments about secrets
    r'#.*token',  # Comments about tokens
    r'#.*key',  # Comments about keys
    r'EXAMPLE_',  # Example values
    r'example_',  # Example values
    r'your[_-]?api[_-]?key',  # Placeholder text
    r'<[A-Z_]+>',  # Placeholder in angle brackets
    r'\$\{[^}]+\}',  # Environment variable references
    r'process\.env\.',  # Node.js env access
    r'\.env\.',  # dotenv references
    r'placeholder',  # Placeholder values
    r'changeme',  # Placeholder values
    r'xxx+',  # Placeholder patterns
    r'\*{4,}',  # Redacted values
]


class SecretScanner:
    """Scans files and git diffs for leaked credentials.

    Attributes:
        allowlist: Configuration for false positive suppression
        patterns: Compiled regex patterns for secret detection
        ignore_patterns: Compiled patterns for false positive detection
    """

    def __init__(self, allowlist: Optional[AllowlistConfig] = None):
        """Initialize the secret scanner.

        Args:
            allowlist: Optional allowlist configuration
        """
        self.allowlist = allowlist or AllowlistConfig()
        self.patterns = [
            (re.compile(pattern), secret_type, confidence)
            for pattern, secret_type, confidence in SECRET_PATTERNS
        ]
        self.ignore_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in IGNORE_PATTERNS
        ]

    def _should_ignore_line(self, line: str) -> bool:
        """Check if a line should be ignored as a false positive.

        Args:
            line: The line to check

        Returns:
            True if the line should be ignored
        """
        for pattern in self.ignore_patterns:
            if pattern.search(line):
                return True
        return False

    def _should_ignore_match(self, match: str) -> bool:
        """Check if a match should be ignored.

        Args:
            match: The matched value

        Returns:
            True if the match should be ignored
        """
        # Check allowlist patterns
        if self.allowlist.is_allowed_pattern(match):
            return True

        # Ignore very short matches (likely false positives)
        if len(match) < 8:
            return True

        # Ignore matches that are all the same character
        if len(set(match)) <= 2:
            return True

        return False

    def scan_file(self, path: Path) -> list[SecretMatch]:
        """Scan a file for potential secrets.

        Args:
            path: Path to the file to scan

        Returns:
            List of SecretMatch objects for detected secrets
        """
        matches = []

        # Check if file should be skipped
        if self.allowlist.is_allowed_file(str(path)):
            return matches

        # Skip binary files
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return matches

        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip lines matching ignore patterns
            if self._should_ignore_line(line):
                continue

            # Check each secret pattern
            for pattern, secret_type, confidence in self.patterns:
                for match in pattern.finditer(line):
                    # Get the actual matched value
                    matched_value = match.group(1) if match.lastindex else match.group(0)

                    # Skip if match should be ignored
                    if self._should_ignore_match(matched_value):
                        continue

                    matches.append(SecretMatch(
                        secret_type=secret_type,
                        file_path=str(path),
                        line_number=line_num,
                        line_content=line,
                        match=matched_value,
                        confidence=confidence,
                    ))

        return matches

    def scan_diff(self, diff: str) -> list[SecretMatch]:
        """Scan a git diff for secrets in newly added lines.

        Args:
            diff: The git diff output

        Returns:
            List of SecretMatch objects for detected secrets
        """
        matches = []
        current_file = ""
        line_num = 0

        for line in diff.split('\n'):
            # Track current file
            if line.startswith('+++ b/'):
                current_file = line[6:]
                continue

            # Track line numbers from hunk headers
            if line.startswith('@@'):
                # Parse @@ -old,count +new,count @@
                hunk_match = re.search(r'\+(\d+)', line)
                if hunk_match:
                    line_num = int(hunk_match.group(1)) - 1
                continue

            # Only check added lines
            if line.startswith('+') and not line.startswith('+++'):
                line_num += 1
                content = line[1:]  # Remove the + prefix

                # Skip if file should be ignored
                if self.allowlist.is_allowed_file(current_file):
                    continue

                # Skip lines matching ignore patterns
                if self._should_ignore_line(content):
                    continue

                # Check each pattern
                for pattern, secret_type, confidence in self.patterns:
                    for match in pattern.finditer(content):
                        matched_value = match.group(1) if match.lastindex else match.group(0)

                        if self._should_ignore_match(matched_value):
                            continue

                        matches.append(SecretMatch(
                            secret_type=secret_type,
                            file_path=current_file,
                            line_number=line_num,
                            line_content=content,
                            match=matched_value,
                            confidence=confidence,
                        ))
            elif not line.startswith('-'):
                # Context line (unchanged), increment line number
                line_num += 1

        return matches

    def scan_staged(self, repo_root: Optional[Path] = None) -> list[SecretMatch]:
        """Scan all staged changes for secrets.

        Args:
            repo_root: Optional repository root path

        Returns:
            List of SecretMatch objects for detected secrets
        """
        cwd = repo_root or Path.cwd()

        # Get staged diff
        result = subprocess.run(
            ['git', 'diff', '--cached', '--unified=0'],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return []

        return self.scan_diff(result.stdout)

    def scan_commit_range(
        self,
        base_ref: str = "HEAD",
        repo_root: Optional[Path] = None
    ) -> list[SecretMatch]:
        """Scan commits since a reference for secrets.

        Args:
            base_ref: Git reference to compare against
            repo_root: Optional repository root path

        Returns:
            List of SecretMatch objects for detected secrets
        """
        cwd = repo_root or Path.cwd()

        # Get diff since base_ref
        result = subprocess.run(
            ['git', 'diff', base_ref, '--unified=0'],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return []

        return self.scan_diff(result.stdout)

    def scan_directory(
        self,
        directory: Path,
        extensions: Optional[list[str]] = None
    ) -> list[SecretMatch]:
        """Scan all files in a directory for secrets.

        Args:
            directory: Directory to scan
            extensions: Optional list of file extensions to scan

        Returns:
            List of SecretMatch objects for detected secrets
        """
        matches = []

        # Default extensions to scan
        if extensions is None:
            extensions = [
                '.py', '.js', '.ts', '.jsx', '.tsx',
                '.json', '.yaml', '.yml', '.toml',
                '.env', '.conf', '.config', '.cfg',
                '.sh', '.bash', '.zsh',
                '.rb', '.go', '.rs', '.java',
                '.php', '.cs', '.cpp', '.c', '.h',
            ]

        for path in directory.rglob('*'):
            # Skip directories
            if path.is_dir():
                continue

            # Skip files without matching extensions
            if extensions and path.suffix.lower() not in extensions:
                continue

            # Skip common non-code directories
            if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build']
                   for part in path.parts):
                continue

            matches.extend(self.scan_file(path))

        return matches


def format_scan_results(matches: list[SecretMatch], verbose: bool = False) -> str:
    """Format scan results for display.

    Args:
        matches: List of SecretMatch objects
        verbose: Whether to show detailed output

    Returns:
        Formatted string for display
    """
    if not matches:
        return "No secrets detected."

    lines = [f"Found {len(matches)} potential secret(s):\n"]

    # Group by file
    by_file: dict[str, list[SecretMatch]] = {}
    for match in matches:
        by_file.setdefault(match.file_path, []).append(match)

    for file_path, file_matches in sorted(by_file.items()):
        lines.append(f"\n{file_path}:")
        for match in sorted(file_matches, key=lambda m: m.line_number):
            if verbose:
                lines.append(f"  Line {match.line_number}: [{match.secret_type.value}]")
                lines.append(f"    {match.line_redacted.strip()}")
                lines.append(f"    Confidence: {match.confidence:.0%}")
            else:
                lines.append(f"  :{match.line_number}: {match.secret_type.value}")

    return '\n'.join(lines)
