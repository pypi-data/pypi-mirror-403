"""Command allowlist system for safe autonomous execution.

This module provides command classification:
- ALLOW: Safe commands that execute without prompts
- REVIEW: Risky commands that require confirmation
- BLOCK: Dangerous commands that are rejected
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class CommandDecision(Enum):
    """Decision for a command check."""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


@dataclass
class CheckResult:
    """Full result of a command check."""

    decision: CommandDecision
    reason: Optional[str] = None
    matched_rule: Optional[str] = None
    command: str = ""


# Default allowlist configuration
DEFAULT_ALLOWLIST = {
    "commands": {
        "always_allowed": [
            # Git read operations
            "git status",
            "git diff",
            "git log",
            "git branch",
            "git show",
            "git remote",
            "git fetch",
            # Testing
            "pytest",
            "python -m pytest",
            # PairCoder
            "bpsai-pair",
            # Read-only utilities
            "ls",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "wc",
            "which",
            "pwd",
            "echo",
            "env",
            "printenv",
            # Python read operations
            "python --version",
            "python -c",
            "pip list",
            "pip show",
            "pip freeze",
        ],
        "require_review": [
            # Git write operations
            "git push",
            "git commit",
            "git merge",
            "git rebase",
            "git reset",
            "git checkout",
            "git stash",
            # Package management
            "pip install",
            "pip uninstall",
            "npm install",
            "npm uninstall",
            "yarn add",
            "cargo add",
            # Docker
            "docker",
            # File operations
            "mv",
            "cp",
            "mkdir",
            "touch",
            # Network
            "curl",
            "wget",
        ],
        "always_blocked": [
            # Destructive operations
            "rm -rf /",
            "rm -rf /*",
            "rm -rf ~",
            "rm -rf $HOME",
            # Privileged operations
            "sudo rm",
            "sudo chmod",
            "sudo chown",
            # Remote code execution
            "curl | bash",
            "curl | sh",
            "wget | bash",
            "wget | sh",
            # System modification
            "mkfs",
            "dd if=",
            ":(){ :|:& };:",  # Fork bomb
        ],
        "patterns": {
            "blocked": [
                r"rm\s+-rf\s+/[^.]",  # rm -rf on absolute paths (not ./)
                r"curl.*\|\s*(ba)?sh",  # curl piped to shell
                r"wget.*\|\s*(ba)?sh",  # wget piped to shell
                r"sudo\s+rm",  # sudo rm anything
                r"docker.*--privileged",  # privileged docker
                r"chmod\s+777",  # overly permissive chmod
                r">\s*/etc/",  # writing to /etc
                r">\s*/usr/",  # writing to /usr
            ],
            "review": [
                r"rm\s+-rf",  # any rm -rf needs review
                r"git\s+push.*--force",  # force push
                r"git\s+reset.*--hard",  # hard reset
            ],
        },
    }
}

# Reasons for blocking specific patterns
BLOCK_REASONS = {
    r"rm\s+-rf\s+/": "Recursive deletion of system directories could destroy the entire system.",
    r"rm\s+-rf": "Recursive forced deletion is dangerous and could cause data loss.",
    r"sudo\s+rm": "Privileged file deletion bypasses safety checks and could damage the system.",
    r"curl.*\|\s*(ba)?sh": "Piping remote content directly to shell allows arbitrary code execution.",
    r"wget.*\|\s*(ba)?sh": "Piping remote content directly to shell allows arbitrary code execution.",
    r"docker.*--privileged": "Privileged Docker containers can escape isolation and access the host system.",
    r"chmod\s+777": "Setting world-writable permissions creates security vulnerabilities.",
    r">\s*/etc/": "Writing to system configuration could break the system.",
    r">\s*/usr/": "Writing to system directories could break installed software.",
    "rm -rf /": "This would delete the entire filesystem.",
    "sudo rm": "Privileged deletion operations are blocked for safety.",
    "curl | bash": "Remote code execution via piped shell is dangerous.",
    "curl | sh": "Remote code execution via piped shell is dangerous.",
    "wget | bash": "Remote code execution via piped shell is dangerous.",
    "wget | sh": "Remote code execution via piped shell is dangerous.",
}


@dataclass
class AllowlistManager:
    """Manages command allowlist for security checks.

    Attributes:
        always_allowed: Commands that execute without prompts
        always_blocked: Commands that are always rejected
        require_review: Commands that need confirmation
        blocked_patterns: Regex patterns for blocked commands
        review_patterns: Regex patterns for commands needing review
    """

    config_path: Optional[Path] = None
    always_allowed: list[str] = field(default_factory=list)
    always_blocked: list[str] = field(default_factory=list)
    require_review: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)
    review_patterns: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Load configuration after initialization."""
        config = self._load_config()
        commands = config.get("commands", {})

        self.always_allowed = commands.get("always_allowed", [])
        self.always_blocked = commands.get("always_blocked", [])
        self.require_review = commands.get("require_review", [])

        patterns = commands.get("patterns", {})
        self.blocked_patterns = patterns.get("blocked", [])
        self.review_patterns = patterns.get("review", [])

    def _load_config(self) -> dict:
        """Load configuration from file or use defaults."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, encoding='utf-8') as f:
                    return yaml.safe_load(f) or DEFAULT_ALLOWLIST
            except Exception:
                return DEFAULT_ALLOWLIST
        return DEFAULT_ALLOWLIST

    def _normalize_command(self, command: str) -> str:
        """Normalize command string for matching."""
        # Strip and collapse whitespace
        return " ".join(command.split())

    def _matches_list(self, command: str, patterns: list[str]) -> Optional[str]:
        """Check if command matches any pattern in the list.

        Returns the matched pattern or None.
        """
        cmd_normalized = self._normalize_command(command)
        cmd_lower = cmd_normalized.lower()

        for pattern in patterns:
            pattern_lower = pattern.lower()

            # Exact match
            if cmd_lower == pattern_lower:
                return pattern

            # Prefix match (command starts with pattern)
            if cmd_lower.startswith(pattern_lower + " ") or cmd_lower.startswith(
                pattern_lower
            ):
                # Handle patterns like "git status" matching "git status --short"
                if pattern_lower.endswith("*"):
                    # Wildcard pattern
                    prefix = pattern_lower.rstrip("*").rstrip()
                    if cmd_lower.startswith(prefix):
                        return pattern
                elif cmd_lower == pattern_lower or cmd_lower.startswith(
                    pattern_lower + " "
                ):
                    return pattern

            # Glob-style matching
            if "*" in pattern:
                # Convert glob to regex for matching
                glob_pattern = pattern.replace("*", ".*")
                if re.match(glob_pattern, cmd_normalized, re.IGNORECASE):
                    return pattern

            # Substring match for blocked commands (e.g., "curl | bash" anywhere)
            if pattern_lower in cmd_lower:
                return pattern

        return None

    def _matches_regex_patterns(
        self, command: str, patterns: list[str]
    ) -> Optional[str]:
        """Check if command matches any regex pattern.

        Returns the matched pattern or None.
        """
        cmd_normalized = self._normalize_command(command)

        for pattern in patterns:
            try:
                if re.search(pattern, cmd_normalized, re.IGNORECASE):
                    return pattern
            except re.error:
                # Invalid regex, skip
                continue

        return None

    def check_command(self, command: str) -> CommandDecision:
        """Check a command and return the decision.

        Args:
            command: The command string to check

        Returns:
            CommandDecision: ALLOW, REVIEW, or BLOCK
        """
        return self.check_command_full(command).decision

    def check_command_full(self, command: str) -> CheckResult:
        """Check a command and return full details.

        Args:
            command: The command string to check

        Returns:
            CheckResult with decision, reason, and matched rule
        """
        cmd_normalized = self._normalize_command(command)

        # Check blocked patterns first (highest priority)
        matched = self._matches_regex_patterns(cmd_normalized, self.blocked_patterns)
        if matched:
            return CheckResult(
                decision=CommandDecision.BLOCK,
                reason=BLOCK_REASONS.get(matched, f"Matches blocked pattern: {matched}"),
                matched_rule=f"pattern:{matched}",
                command=cmd_normalized,
            )

        # Check blocked list
        matched = self._matches_list(cmd_normalized, self.always_blocked)
        if matched:
            return CheckResult(
                decision=CommandDecision.BLOCK,
                reason=BLOCK_REASONS.get(matched, f"Command is in blocked list: {matched}"),
                matched_rule=f"blocked:{matched}",
                command=cmd_normalized,
            )

        # Check allowed list
        matched = self._matches_list(cmd_normalized, self.always_allowed)
        if matched:
            return CheckResult(
                decision=CommandDecision.ALLOW,
                reason=None,
                matched_rule=f"allowed:{matched}",
                command=cmd_normalized,
            )

        # Check review patterns
        matched = self._matches_regex_patterns(cmd_normalized, self.review_patterns)
        if matched:
            return CheckResult(
                decision=CommandDecision.REVIEW,
                reason=f"Matches review pattern: {matched}",
                matched_rule=f"pattern:{matched}",
                command=cmd_normalized,
            )

        # Check review list
        matched = self._matches_list(cmd_normalized, self.require_review)
        if matched:
            return CheckResult(
                decision=CommandDecision.REVIEW,
                reason=f"Command requires review: {matched}",
                matched_rule=f"review:{matched}",
                command=cmd_normalized,
            )

        # Default: unknown commands require review
        return CheckResult(
            decision=CommandDecision.REVIEW,
            reason="Unknown command - requires review",
            matched_rule="default:unknown",
            command=cmd_normalized,
        )

    def get_blocked_reason(self, command: str) -> Optional[str]:
        """Get the reason a command is blocked.

        Args:
            command: The command string to check

        Returns:
            Reason string if blocked, None if not blocked
        """
        result = self.check_command_full(command)
        if result.decision == CommandDecision.BLOCK:
            return result.reason
        return None

    def add_to_allowlist(self, command_or_pattern: str) -> None:
        """Add a command or pattern to the always_allowed list.

        Args:
            command_or_pattern: Command string or glob pattern to allow
        """
        if command_or_pattern not in self.always_allowed:
            self.always_allowed.append(command_or_pattern)

    def add_to_blocklist(self, command_or_pattern: str, reason: str = "") -> None:
        """Add a command or pattern to the always_blocked list.

        Args:
            command_or_pattern: Command string or glob pattern to block
            reason: Optional reason for blocking
        """
        if command_or_pattern not in self.always_blocked:
            self.always_blocked.append(command_or_pattern)
            if reason:
                BLOCK_REASONS[command_or_pattern] = reason

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file.

        Args:
            path: Path to save config (uses config_path if not specified)
        """
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No path specified for saving config")

        config = {
            "commands": {
                "always_allowed": self.always_allowed,
                "always_blocked": self.always_blocked,
                "require_review": self.require_review,
                "patterns": {
                    "blocked": self.blocked_patterns,
                    "review": self.review_patterns,
                },
            }
        }

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
