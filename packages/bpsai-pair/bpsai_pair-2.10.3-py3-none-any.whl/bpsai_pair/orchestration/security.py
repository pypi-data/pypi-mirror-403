"""
Security Agent Implementation.

Provides the SecurityAgent class for pre-execution security review.
The security agent operates in read-only mode (permissionMode: plan) and
acts as a gatekeeper that can block unsafe operations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .invoker import AgentDefinition, AgentInvoker, InvocationResult

logger = logging.getLogger(__name__)

# Default location for agent definitions
DEFAULT_AGENTS_DIR = ".claude/agents"


class SecurityAction(Enum):
    """
    Security decision action types.

    Ordering: ALLOW < WARN < BLOCK (by severity)
    """

    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"

    def __lt__(self, other: "SecurityAction") -> bool:
        order = [SecurityAction.ALLOW, SecurityAction.WARN, SecurityAction.BLOCK]
        return order.index(self) < order.index(other)

    @classmethod
    def from_string(cls, value: str) -> "SecurityAction":
        """
        Create action from string value.

        Handles various formats:
        - "allow", "allowed", "ok" -> ALLOW
        - "warn", "warning", "review" -> WARN
        - "block", "blocked", "deny", "denied" -> BLOCK
        """
        value_lower = value.lower().strip()

        if value_lower in ("allow", "allowed", "ok", "pass", "passed"):
            return cls.ALLOW
        elif value_lower in ("warn", "warning", "review", "caution"):
            return cls.WARN
        elif value_lower in ("block", "blocked", "deny", "denied", "reject", "rejected"):
            return cls.BLOCK

        # Default to BLOCK for safety (fail safe)
        return cls.BLOCK


@dataclass
class SecurityFinding:
    """
    A single security finding.

    Represents a security issue or concern found during review
    with severity, SOC2 control references, and suggested fixes.
    """

    action: SecurityAction
    severity: str  # critical, high, medium, low
    reason: str
    details: list[str] = field(default_factory=list)
    soc2_controls: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action.value,
            "severity": self.severity,
            "reason": self.reason,
            "details": self.details,
            "soc2_controls": self.soc2_controls,
            "suggested_fixes": self.suggested_fixes,
        }


@dataclass
class SecurityDecision:
    """
    Structured output from the security agent.

    Contains the overall decision (ALLOW/WARN/BLOCK), individual findings,
    and summary information for audit logging.
    """

    action: SecurityAction
    findings: list[SecurityFinding] = field(default_factory=list)
    summary: str = ""
    raw_output: str = ""

    @property
    def is_allowed(self) -> bool:
        """Check if the operation is allowed to proceed."""
        return self.action == SecurityAction.ALLOW

    @property
    def is_blocked(self) -> bool:
        """Check if the operation is blocked."""
        return self.action == SecurityAction.BLOCK

    @property
    def has_warnings(self) -> bool:
        """Check if the decision has any warnings."""
        return self.action == SecurityAction.WARN or any(
            f.action == SecurityAction.WARN for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action.value,
            "is_allowed": self.is_allowed,
            "is_blocked": self.is_blocked,
            "has_warnings": self.has_warnings,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }

    @classmethod
    def allow(cls, summary: str = "Security checks passed.") -> "SecurityDecision":
        """Create an allowed decision with no issues."""
        return cls(
            action=SecurityAction.ALLOW,
            findings=[],
            summary=summary,
        )

    @classmethod
    def block(
        cls,
        reason: str,
        soc2_controls: Optional[list[str]] = None,
        suggested_fixes: Optional[list[str]] = None,
        details: Optional[list[str]] = None,
        severity: str = "critical",
    ) -> "SecurityDecision":
        """
        Create a blocked decision with reason.

        Args:
            reason: Why the operation is blocked
            soc2_controls: SOC2 control references
            suggested_fixes: Remediation steps
            details: Additional details about the issue
            severity: Severity level (critical, high, medium, low)
        """
        finding = SecurityFinding(
            action=SecurityAction.BLOCK,
            severity=severity,
            reason=reason,
            details=details or [],
            soc2_controls=soc2_controls or [],
            suggested_fixes=suggested_fixes or [],
        )
        return cls(
            action=SecurityAction.BLOCK,
            findings=[finding],
            summary=f"BLOCKED: {reason}",
        )

    @classmethod
    def warn(
        cls,
        reason: str,
        soc2_controls: Optional[list[str]] = None,
        suggested_fixes: Optional[list[str]] = None,
        details: Optional[list[str]] = None,
        severity: str = "medium",
    ) -> "SecurityDecision":
        """
        Create a warning decision requiring review.

        Args:
            reason: Why this requires review
            soc2_controls: SOC2 control references
            suggested_fixes: Suggested remediation steps
            details: Additional details
            severity: Severity level
        """
        finding = SecurityFinding(
            action=SecurityAction.WARN,
            severity=severity,
            reason=reason,
            details=details or [],
            soc2_controls=soc2_controls or [],
            suggested_fixes=suggested_fixes or [],
        )
        return cls(
            action=SecurityAction.WARN,
            findings=[finding],
            summary=f"REQUIRES REVIEW: {reason}",
        )

    @classmethod
    def from_raw_text(cls, raw_text: str) -> "SecurityDecision":
        """
        Parse security decision from raw markdown output.

        Attempts to extract structured information from the security agent's
        markdown-formatted response.

        Args:
            raw_text: Raw markdown text from security agent output

        Returns:
            SecurityDecision with parsed content
        """
        findings: list[SecurityFinding] = []
        summary = ""
        action = SecurityAction.ALLOW

        # Detect BLOCKED response
        blocked_match = re.search(
            r"##\s*🛑\s*BLOCKED[:\s]*(.*?)(?:\n|$)",
            raw_text,
            re.IGNORECASE
        )
        if blocked_match:
            action = SecurityAction.BLOCK
            summary = f"BLOCKED: {blocked_match.group(1).strip()}"

            # Extract reason
            reason_match = re.search(
                r"\*\*Reason:\*\*\s*(.*?)(?:\n\n|\n\*\*|$)",
                raw_text,
                re.DOTALL | re.IGNORECASE
            )
            reason = reason_match.group(1).strip() if reason_match else "Security issue detected"

            # Extract details
            details = _extract_list_items(raw_text, r"\*\*Detected:\*\*")

            # Extract SOC2 controls
            soc2_controls = _extract_soc2_controls(raw_text)

            # Extract suggested fixes
            suggested_fixes_match = re.search(
                r"\*\*To Proceed:\*\*\s*(.*?)(?:\n##|\Z)",
                raw_text,
                re.DOTALL | re.IGNORECASE
            )
            suggested_fixes = []
            if suggested_fixes_match:
                suggested_fixes = [suggested_fixes_match.group(1).strip()]

            findings.append(SecurityFinding(
                action=SecurityAction.BLOCK,
                severity="critical",
                reason=reason,
                details=details,
                soc2_controls=soc2_controls,
                suggested_fixes=suggested_fixes,
            ))

        # Detect WARNING/REQUIRES REVIEW response
        warn_match = re.search(
            r"##\s*⚠️\s*REQUIRES\s*REVIEW[:\s]*(.*?)(?:\n|$)",
            raw_text,
            re.IGNORECASE
        )
        if warn_match and action != SecurityAction.BLOCK:
            action = SecurityAction.WARN
            summary = f"REQUIRES REVIEW: {warn_match.group(1).strip()}"

            # Extract concern
            concern_match = re.search(
                r"\*\*Concern:\*\*\s*(.*?)(?:\n\n|\n\*\*|$)",
                raw_text,
                re.DOTALL | re.IGNORECASE
            )
            reason = concern_match.group(1).strip() if concern_match else "Requires review"

            # Extract details
            details = _extract_list_items(raw_text, r"\*\*Details:\*\*")

            # Extract SOC2 controls
            soc2_controls = _extract_soc2_controls(raw_text)

            # Extract risk level
            risk_match = re.search(
                r"\*\*Risk\s*Level:\*\*\s*(\w+)",
                raw_text,
                re.IGNORECASE
            )
            severity = risk_match.group(1).lower() if risk_match else "medium"

            findings.append(SecurityFinding(
                action=SecurityAction.WARN,
                severity=severity,
                reason=reason,
                details=details,
                soc2_controls=soc2_controls,
            ))

        # Detect ALLOWED response
        allowed_match = re.search(
            r"##\s*✅\s*ALLOWED[:\s]*(.*?)(?:\n|$)",
            raw_text,
            re.IGNORECASE
        )
        if allowed_match and action == SecurityAction.ALLOW:
            summary = "Security checks passed."

        return cls(
            action=action,
            findings=findings,
            summary=summary or "Security review complete.",
            raw_output=raw_text,
        )

    def format_message(self) -> str:
        """Format the decision as a human-readable message."""
        lines = []

        if self.is_blocked:
            lines.append(f"🛑 {self.summary}")
            for finding in self.findings:
                if finding.action == SecurityAction.BLOCK:
                    lines.append(f"\nReason: {finding.reason}")
                    if finding.details:
                        lines.append("Detected:")
                        for detail in finding.details:
                            lines.append(f"  - {detail}")
                    if finding.soc2_controls:
                        lines.append(f"SOC2 Controls: {', '.join(finding.soc2_controls)}")
                    if finding.suggested_fixes:
                        lines.append("To Proceed:")
                        for fix in finding.suggested_fixes:
                            lines.append(f"  - {fix}")

        elif self.has_warnings:
            lines.append(f"⚠️ {self.summary}")
            for finding in self.findings:
                if finding.action == SecurityAction.WARN:
                    lines.append(f"\nConcern: {finding.reason}")
                    if finding.details:
                        lines.append("Details:")
                        for detail in finding.details:
                            lines.append(f"  - {detail}")
                    if finding.soc2_controls:
                        lines.append(f"SOC2 Controls: {', '.join(finding.soc2_controls)}")

        else:
            lines.append(f"✅ {self.summary}")

        return "\n".join(lines)


def _extract_list_items(text: str, header_pattern: str) -> list[str]:
    """Extract list items following a header."""
    items = []
    header_match = re.search(
        f"{header_pattern}\\s*(.*?)(?:\\n\\*\\*|\\n##|\\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if header_match:
        content = header_match.group(1)
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                items.append(line.lstrip("-*").strip())
    return items


def _extract_soc2_controls(text: str) -> list[str]:
    """Extract SOC2 control references from text."""
    controls = []
    # Look for SOC2 Controls header
    soc2_match = re.search(
        r"\*\*SOC2\s*Controls?:\*\*\s*(.*?)(?:\n\n|\n\*\*|$)",
        text,
        re.IGNORECASE
    )
    if soc2_match:
        controls_text = soc2_match.group(1)
        # Extract CC*.* patterns
        controls = re.findall(r"CC\d+\.\d+", controls_text)
    return controls


# Command patterns for trigger detection
ALWAYS_BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/(?!\.|tmp)",  # rm -rf / (not ./ or /tmp)
    r"curl\s+.*\|\s*(?:ba)?sh",  # curl | bash
    r"wget\s+.*\|\s*(?:ba)?sh",  # wget | bash
    r"sudo\s+rm",  # sudo rm
]

REQUIRES_REVIEW_PATTERNS = [
    r"pip\s+install",
    r"npm\s+install",
    r"git\s+push",
    r"git\s+commit",
    r"docker\s+",
    r"chmod\s+",
    r"chown\s+",
]

ALWAYS_ALLOWED_PATTERNS = [
    r"^git\s+status$",
    r"^git\s+diff",
    r"^git\s+log",
    r"^pytest\s+",
    r"^bpsai-pair\s+",
    r"^ls\s+",
    r"^cat\s+[^|]*$",  # cat without pipe
    r"^grep\s+",
]

AUTH_KEYWORDS = [
    "auth", "login", "credential", "password", "secret", "token",
    "api key", "apikey", "api_key", "oauth", "jwt",
]


@dataclass
class SecurityAgent:
    """
    Security agent for pre-execution review.

    Uses the AgentInvoker framework to invoke the security agent
    defined in .claude/agents/security.md. Always operates in
    read-only 'plan' permission mode.

    Example:
        >>> agent = SecurityAgent()
        >>> decision = agent.review_command("rm -rf /tmp/test")
        >>> if decision.is_blocked:
        ...     print(f"Blocked: {decision.summary}")

        >>> # Or review code changes
        >>> decision = agent.review_code(diff="...", changed_files=["auth.py"])
        >>> for finding in decision.findings:
        ...     print(f"{finding.severity}: {finding.reason}")
    """

    agents_dir: Path = field(default_factory=lambda: Path(DEFAULT_AGENTS_DIR))
    working_dir: Optional[Path] = None
    timeout_seconds: int = 300
    agent_name: str = "security"
    permission_mode: str = "plan"  # Always read-only

    _invoker: Optional[AgentInvoker] = field(default=None, repr=False)
    _agent_definition: Optional[AgentDefinition] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize the agent invoker."""
        if not self.agents_dir.is_absolute():
            base = self.working_dir or Path.cwd()
            self.agents_dir = base / self.agents_dir

    def _get_invoker(self) -> AgentInvoker:
        """Get or create the AgentInvoker instance."""
        if self._invoker is None:
            self._invoker = AgentInvoker(
                agents_dir=self.agents_dir,
                working_dir=self.working_dir,
                timeout_seconds=self.timeout_seconds,
            )
        return self._invoker

    def load_agent_definition(self) -> AgentDefinition:
        """
        Load the security agent definition.

        Returns:
            AgentDefinition for the security agent
        """
        if self._agent_definition is None:
            self._agent_definition = self._get_invoker().load_agent(self.agent_name)
        return self._agent_definition

    def build_context(
        self,
        command: str = "",
        diff: str = "",
        changed_files: Optional[list[str]] = None,
        operation_type: str = "review",
    ) -> str:
        """
        Build context string for security review.

        Combines command, code diff, and operation type into a
        comprehensive context string for the security agent.

        Args:
            command: Command to review
            diff: Git diff output to review
            changed_files: List of changed file paths
            operation_type: Type of operation (command, commit, pr)

        Returns:
            Combined context string
        """
        context_parts = []

        context_parts.append(f"## Operation Type: {operation_type}")

        if command:
            context_parts.append(f"## Command to Review\n\n```bash\n{command}\n```")

        if diff:
            context_parts.append(f"## Code Diff\n\n```diff\n{diff}\n```")

        if changed_files:
            files_list = "\n".join(f"- {f}" for f in changed_files)
            context_parts.append(f"## Changed Files\n\n{files_list}")

        return "\n\n---\n\n".join(context_parts) if context_parts else "No context provided"

    def invoke(self, prompt: str, **kwargs) -> InvocationResult:
        """
        Invoke the security agent with a prompt.

        Args:
            prompt: The security review prompt/task description
            **kwargs: Additional arguments for the invoker

        Returns:
            InvocationResult with output and metadata
        """
        invoker = self._get_invoker()
        return invoker.invoke(self.agent_name, prompt, **kwargs)

    def review_command(self, command: str) -> SecurityDecision:
        """
        Review a command for security issues.

        Args:
            command: The command to review

        Returns:
            SecurityDecision indicating if execution should proceed
        """
        context = self.build_context(command=command, operation_type="command")

        review_prompt = f"""Review the following command for security issues before execution.

You are a security gatekeeper. Analyze this command and determine:
- Should it be BLOCKED? (dangerous, destructive, leaks secrets)
- Should it require REVIEW? (installs packages, modifies permissions, network ops)
- Is it ALLOWED? (safe, standard development command)

Respond with your decision using the format:
- ## 🛑 BLOCKED: [type] for dangerous commands
- ## ⚠️ REQUIRES REVIEW: [type] for risky commands
- ## ✅ ALLOWED: [type] for safe commands

Include:
- **Reason:** explanation
- **SOC2 Controls:** relevant controls (CC6.1, CC7.1, etc.)
- **To Proceed:** (for blocks) what the user should do instead

---

{context}"""

        result = self.invoke(review_prompt)

        if not result.success:
            logger.error(f"Security review failed: {result.error}")
            # Fail safe: block on error
            return SecurityDecision.block(
                reason=f"Security review failed: {result.error}",
                soc2_controls=["CC6.1"],
                suggested_fixes=["Retry the security review", "Contact administrator"],
            )

        return SecurityDecision.from_raw_text(result.output)

    def review_code(
        self,
        diff: str = "",
        changed_files: Optional[list[str]] = None,
    ) -> SecurityDecision:
        """
        Review code changes for security issues.

        Args:
            diff: Git diff output to review
            changed_files: List of changed file paths

        Returns:
            SecurityDecision with findings
        """
        context = self.build_context(
            diff=diff,
            changed_files=changed_files,
            operation_type="commit",
        )

        review_prompt = f"""Review the following code changes for security issues before commit.

You are a security gatekeeper. Analyze these changes for:
- Hardcoded secrets (API keys, passwords, tokens)
- Injection vulnerabilities (SQL, command, path traversal)
- Dangerous patterns (unsafe deserialization, RCE vectors)
- Sensitive data in logs or error messages

Respond with your decision using the format:
- ## 🛑 BLOCKED: [type] for security vulnerabilities
- ## ⚠️ REQUIRES REVIEW: [type] for risky patterns
- ## ✅ ALLOWED: [type] for clean code

Include:
- **Reason:** or **Concern:** explanation
- **Detected:** or **Details:** specific issues found
- **SOC2 Controls:** relevant controls
- **To Proceed:** remediation steps

---

{context}"""

        result = self.invoke(review_prompt)

        if not result.success:
            logger.error(f"Security review failed: {result.error}")
            return SecurityDecision.block(
                reason=f"Security review failed: {result.error}",
                soc2_controls=["CC7.1"],
                suggested_fixes=["Retry the security review"],
            )

        return SecurityDecision.from_raw_text(result.output)


def should_trigger_security(
    command: Optional[str] = None,
    task_title: Optional[str] = None,
    pre_commit: bool = False,
    pre_pr: bool = False,
    explicit_request: bool = False,
) -> bool:
    """
    Determine if the security agent should be triggered.

    Trigger conditions:
    - Command matches blocked or review patterns
    - Pre-commit or pre-PR hook
    - Task involves auth/credentials
    - User explicitly requests review

    Args:
        command: Command to check
        task_title: Title of the task
        pre_commit: Whether this is a pre-commit review
        pre_pr: Whether this is a pre-PR review
        explicit_request: Whether user explicitly requested review

    Returns:
        True if security agent should be triggered
    """
    if explicit_request:
        return True

    if pre_commit or pre_pr:
        return True

    if command:
        # Check against always-blocked patterns
        for pattern in ALWAYS_BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        # Check against requires-review patterns
        for pattern in REQUIRES_REVIEW_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        # Check against always-allowed patterns (no trigger needed)
        for pattern in ALWAYS_ALLOWED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False

    if task_title:
        title_lower = task_title.lower()
        if any(keyword in title_lower for keyword in AUTH_KEYWORDS):
            return True

    return False


def invoke_security(
    command: Optional[str] = None,
    diff: Optional[str] = None,
    changed_files: Optional[list[str]] = None,
    working_dir: Optional[Path] = None,
    agents_dir: Optional[Path] = None,
    timeout: int = 300,
) -> SecurityDecision:
    """
    Convenience function for invoking the security agent.

    Can be called with either a command or code diff:
    - With command: Calls review_command()
    - With diff: Calls review_code()

    Args:
        command: Command to review
        diff: Git diff to review
        changed_files: List of changed files
        working_dir: Working directory for the command
        agents_dir: Directory containing agent definitions
        timeout: Timeout in seconds

    Returns:
        SecurityDecision with review results

    Example:
        >>> # Review a command
        >>> decision = invoke_security(command="pip install requests")
        >>> if decision.has_warnings:
        ...     print("Review required")

        >>> # Review code changes
        >>> decision = invoke_security(diff="...", changed_files=["auth.py"])
        >>> if decision.is_blocked:
        ...     print(decision.format_message())
    """
    agent = SecurityAgent(
        agents_dir=agents_dir or Path(DEFAULT_AGENTS_DIR),
        working_dir=working_dir,
        timeout_seconds=timeout,
    )

    if command is not None:
        return agent.review_command(command)

    if diff is not None:
        return agent.review_code(
            diff=diff,
            changed_files=changed_files,
        )

    # Default to allow if nothing to review
    return SecurityDecision.allow()
