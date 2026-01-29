"""
Reviewer Agent Implementation.

Provides the ReviewerAgent class for code review tasks.
The reviewer operates in read-only mode (permissionMode: plan) and
returns structured review feedback.
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


class ReviewSeverity(Enum):
    """
    Severity levels for review items.

    Ordering: INFO < WARNING < BLOCKER
    """

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"

    def __lt__(self, other: "ReviewSeverity") -> bool:
        order = [ReviewSeverity.INFO, ReviewSeverity.WARNING, ReviewSeverity.BLOCKER]
        return order.index(self) < order.index(other)

    @classmethod
    def from_string(cls, value: str) -> "ReviewSeverity":
        """
        Create severity from string value.

        Handles various formats:
        - "info", "consider", "optional" -> INFO
        - "warning", "should fix" -> WARNING
        - "blocker", "error", "must fix" -> BLOCKER
        """
        value_lower = value.lower().strip()

        if value_lower in ("info", "consider", "optional", "suggestion"):
            return cls.INFO
        elif value_lower in ("warning", "should fix", "should-fix", "non-blocking"):
            return cls.WARNING
        elif value_lower in ("blocker", "error", "must fix", "must-fix", "blocking", "critical"):
            return cls.BLOCKER

        return cls.INFO  # Default to INFO for unknown


class ReviewVerdict(Enum):
    """
    Overall verdict for a code review.
    """

    APPROVE = "approve"
    APPROVE_WITH_COMMENTS = "approve_with_comments"
    REQUEST_CHANGES = "request_changes"

    @classmethod
    def from_string(cls, value: str) -> "ReviewVerdict":
        """
        Create verdict from string value.

        Handles various formats like:
        - "approve", "approved", "lgtm"
        - "approve with comments"
        - "request changes", "changes requested"
        """
        value_lower = value.lower().strip()

        if "request" in value_lower or "changes" in value_lower and "approve" not in value_lower:
            return cls.REQUEST_CHANGES
        elif "with comments" in value_lower or "with suggestions" in value_lower:
            return cls.APPROVE_WITH_COMMENTS
        elif "approve" in value_lower or "lgtm" in value_lower:
            return cls.APPROVE

        return cls.REQUEST_CHANGES  # Default to safest option


@dataclass
class ReviewItem:
    """
    A single review item/finding.

    Represents a piece of feedback from the code review
    with severity, location, and suggested fix.
    """

    severity: ReviewSeverity
    file_path: str
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    category: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "message": self.message,
            "suggestion": self.suggestion,
            "category": self.category,
            "code_snippet": self.code_snippet,
        }


@dataclass
class ReviewOutput:
    """
    Structured output from the reviewer agent.

    Contains the review verdict, summary, individual items,
    and positive notes about the code.
    """

    verdict: ReviewVerdict
    summary: str
    items: list[ReviewItem] = field(default_factory=list)
    positive_notes: list[str] = field(default_factory=list)
    raw_output: str = ""

    @property
    def blocker_count(self) -> int:
        """Count of blocker-severity items."""
        return sum(1 for item in self.items if item.severity == ReviewSeverity.BLOCKER)

    @property
    def warning_count(self) -> int:
        """Count of warning-severity items."""
        return sum(1 for item in self.items if item.severity == ReviewSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-severity items."""
        return sum(1 for item in self.items if item.severity == ReviewSeverity.INFO)

    @property
    def has_blockers(self) -> bool:
        """Whether review has any blocker-severity items."""
        return self.blocker_count > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "verdict": self.verdict.value,
            "summary": self.summary,
            "items": [item.to_dict() for item in self.items],
            "positive_notes": self.positive_notes,
            "counts": {
                "blocker": self.blocker_count,
                "warning": self.warning_count,
                "info": self.info_count,
            },
        }

    @classmethod
    def from_raw_text(cls, raw_text: str) -> "ReviewOutput":
        """
        Parse review from raw markdown output.

        Attempts to extract structured information from the reviewer's
        markdown-formatted response.

        Args:
            raw_text: Raw markdown text from reviewer output

        Returns:
            ReviewOutput with parsed content
        """
        items: list[ReviewItem] = []
        positive_notes: list[str] = []
        summary = ""
        verdict = ReviewVerdict.APPROVE

        # Extract summary
        summary_match = re.search(
            r"##\s*Review\s*Summary\s*\n(.*?)(?=\n##|\Z)",
            raw_text,
            re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            summary = summary_match.group(1).strip()

        # Extract must-fix (blocker) items
        blocker_match = re.search(
            r"##\s*🔴\s*Must\s*Fix.*?\n(.*?)(?=\n##|\Z)",
            raw_text,
            re.DOTALL | re.IGNORECASE
        )
        if blocker_match:
            items.extend(_parse_review_items(blocker_match.group(1), ReviewSeverity.BLOCKER))

        # Extract should-fix (warning) items
        warning_match = re.search(
            r"##\s*🟡\s*Should\s*Fix.*?\n(.*?)(?=\n##|\Z)",
            raw_text,
            re.DOTALL | re.IGNORECASE
        )
        if warning_match:
            items.extend(_parse_review_items(warning_match.group(1), ReviewSeverity.WARNING))

        # Extract consider (info) items
        info_match = re.search(
            r"##\s*🟢\s*Consider.*?\n(.*?)(?=\n##|\Z)",
            raw_text,
            re.DOTALL | re.IGNORECASE
        )
        if info_match:
            items.extend(_parse_review_items(info_match.group(1), ReviewSeverity.INFO))

        # Extract positive notes
        positive_match = re.search(
            r"##\s*👍\s*Positive\s*Notes?\s*\n(.*?)(?=\n##|\Z)",
            raw_text,
            re.DOTALL | re.IGNORECASE
        )
        if positive_match:
            notes_text = positive_match.group(1)
            for line in notes_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    note = line.lstrip("-*").strip()
                    if note:
                        positive_notes.append(note)

        # Extract verdict
        verdict_match = re.search(
            r"\*\*Status\*\*:\s*(.*?)(?:\n|$)",
            raw_text,
            re.IGNORECASE
        )
        if verdict_match:
            verdict = ReviewVerdict.from_string(verdict_match.group(1))

        return cls(
            verdict=verdict,
            summary=summary,
            items=items,
            positive_notes=positive_notes,
            raw_output=raw_text,
        )


def _parse_review_items(text: str, severity: ReviewSeverity) -> list[ReviewItem]:
    """
    Parse review items from a section of markdown text.

    Looks for patterns like:
    **[file.py:42]** Issue description
    """
    items = []

    # Pattern to match file:line references
    item_pattern = r"\*\*\[([^\]:]+)(?::(\d+))?\]\*\*\s*(.+?)(?=\n\*\*\[|\n\n|$)"

    for match in re.finditer(item_pattern, text, re.DOTALL):
        file_path = match.group(1).strip()
        line_number = int(match.group(2)) if match.group(2) else None
        content = match.group(3).strip()

        # Extract message and suggestion
        message = content.split("\n")[0].strip()
        suggestion = None

        suggestion_match = re.search(r"Suggestion:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        if suggestion_match:
            suggestion = suggestion_match.group(1).strip()

        items.append(ReviewItem(
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            message=message,
            suggestion=suggestion,
        ))

    return items


def extract_changed_files(diff: str) -> list[str]:
    """
    Extract list of changed files from a git diff.

    Args:
        diff: Git diff output

    Returns:
        List of file paths that were changed
    """
    files = []
    pattern = r"diff --git a/(.+?) b/\1"

    for match in re.finditer(pattern, diff):
        files.append(match.group(1))

    return files


def extract_line_changes(diff: str) -> tuple[list[int], list[int]]:
    """
    Extract line numbers of additions and deletions from a diff.

    Args:
        diff: Git diff output

    Returns:
        Tuple of (added_lines, deleted_lines)
    """
    additions = []
    deletions = []

    # Find hunk headers: @@ -start,count +start,count @@
    hunk_pattern = r"@@ -(\d+),?\d* \+(\d+),?\d* @@"

    current_line = 0
    in_hunk = False

    for line in diff.split("\n"):
        hunk_match = re.match(hunk_pattern, line)
        if hunk_match:
            current_line = int(hunk_match.group(2))
            in_hunk = True
            continue

        if in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                additions.append(current_line)
                current_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions.append(current_line)
                # Don't increment for deletions (they don't exist in new file)
            else:
                current_line += 1

    return additions, deletions


@dataclass
class ReviewerAgent:
    """
    Reviewer agent for code review tasks.

    Uses the AgentInvoker framework to invoke the reviewer agent
    defined in .claude/agents/reviewer.md. Always operates in
    read-only 'plan' permission mode.

    Example:
        >>> reviewer = ReviewerAgent()
        >>> result = reviewer.invoke("Review the authentication changes")
        >>> print(result.output)

        >>> # Or get structured review output
        >>> output = reviewer.review(diff="...", changed_files=["auth.py"])
        >>> for item in output.items:
        ...     print(f"{item.severity}: {item.message}")
    """

    agents_dir: Path = field(default_factory=lambda: Path(DEFAULT_AGENTS_DIR))
    working_dir: Optional[Path] = None
    timeout_seconds: int = 300
    agent_name: str = "reviewer"
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
        Load the reviewer agent definition.

        Returns:
            AgentDefinition for the reviewer agent
        """
        if self._agent_definition is None:
            self._agent_definition = self._get_invoker().load_agent(self.agent_name)
        return self._agent_definition

    def build_context(
        self,
        diff: str = "",
        changed_files: Optional[list[str]] = None,
        include_file_contents: bool = False,
        test_results: Optional[str] = None,
    ) -> str:
        """
        Build context string for reviewer invocation.

        Combines git diff, changed files, and optional test results
        into a comprehensive context string.

        Args:
            diff: Git diff output to review
            changed_files: List of changed file paths
            include_file_contents: Whether to include full file contents
            test_results: Optional test output to include

        Returns:
            Combined context string
        """
        context_parts = []

        # Add diff
        if diff:
            context_parts.append(f"## Git Diff\n\n```diff\n{diff}\n```")

        # Add changed files list
        if changed_files:
            files_list = "\n".join(f"- {f}" for f in changed_files)
            context_parts.append(f"## Changed Files\n\n{files_list}")

            # Include file contents if requested
            if include_file_contents and self.working_dir:
                for file_path in changed_files:
                    full_path = self.working_dir / file_path
                    if full_path.exists():
                        try:
                            content = full_path.read_text(encoding="utf-8")
                            context_parts.append(
                                f"## File: {file_path}\n\n```\n{content}\n```"
                            )
                        except Exception as e:
                            logger.warning(f"Could not read {file_path}: {e}")

        # Add test results
        if test_results:
            context_parts.append(f"## Test Results\n\n```\n{test_results}\n```")

        return "\n\n---\n\n".join(context_parts) if context_parts else "No context provided"

    def invoke(self, prompt: str, **kwargs) -> InvocationResult:
        """
        Invoke the reviewer agent with a prompt.

        Args:
            prompt: The review prompt/task description
            **kwargs: Additional arguments for the invoker

        Returns:
            InvocationResult with output and metadata
        """
        invoker = self._get_invoker()
        return invoker.invoke(self.agent_name, prompt, **kwargs)

    def review(
        self,
        diff: str = "",
        changed_files: Optional[list[str]] = None,
        include_file_contents: bool = False,
        test_results: Optional[str] = None,
    ) -> ReviewOutput:
        """
        Perform a structured code review.

        Builds comprehensive context, invokes the reviewer agent,
        and parses the output into a structured ReviewOutput.

        Args:
            diff: Git diff output to review
            changed_files: List of changed file paths
            include_file_contents: Whether to include full file contents
            test_results: Optional test output to include

        Returns:
            ReviewOutput with structured review feedback
        """
        # Build context
        context = self.build_context(
            diff=diff,
            changed_files=changed_files,
            include_file_contents=include_file_contents,
            test_results=test_results,
        )

        # Add review instructions
        review_prompt = f"""Please review the following code changes.

Your review should include:
1. A brief summary of the changes
2. Any blocking issues that must be fixed (🔴 Must Fix)
3. Suggestions that should be addressed (🟡 Should Fix)
4. Optional improvements to consider (🟢 Consider)
5. Positive notes about the code (👍 Positive Notes)
6. An overall verdict (Approve / Approve with comments / Request changes)

Format your response with these sections:
- ## Review Summary
- ## 🔴 Must Fix (Blocking)
- ## 🟡 Should Fix (Non-blocking)
- ## 🟢 Consider (Optional)
- ## 👍 Positive Notes
- ## Verdict (with **Status**: value)

For each issue, use the format:
**[file.py:line_number]** Issue description

---

{context}"""

        # Invoke reviewer
        result = self.invoke(review_prompt)

        if not result.success:
            logger.error(f"Review invocation failed: {result.error}")
            return ReviewOutput(
                verdict=ReviewVerdict.REQUEST_CHANGES,
                summary=f"Review failed: {result.error}",
                items=[],
                raw_output="",
            )

        # Parse output
        return ReviewOutput.from_raw_text(result.output)


def should_trigger_reviewer(
    task_type: Optional[str] = None,
    task_title: Optional[str] = None,
    pre_pr: bool = False,
    explicit_request: bool = False,
) -> bool:
    """
    Determine if the reviewer agent should be triggered.

    Trigger conditions:
    - Task type is REVIEW
    - Task title contains "review"
    - Pre-PR creation
    - User explicitly requests review

    Args:
        task_type: Type of the task (REVIEW, IMPLEMENT, etc.)
        task_title: Title of the task
        pre_pr: Whether this is a pre-PR review
        explicit_request: Whether user explicitly requested review

    Returns:
        True if reviewer should be triggered
    """
    if explicit_request:
        return True

    if pre_pr:
        return True

    if task_type and task_type.upper() == "REVIEW":
        return True

    if task_title:
        title_lower = task_title.lower()
        trigger_words = ["review", "code review", "pr review", "check code"]
        if any(word in title_lower for word in trigger_words):
            return True

    return False


def invoke_reviewer(
    prompt: Optional[str] = None,
    diff: Optional[str] = None,
    changed_files: Optional[list[str]] = None,
    working_dir: Optional[Path] = None,
    agents_dir: Optional[Path] = None,
    timeout: int = 300,
) -> InvocationResult | ReviewOutput:
    """
    Convenience function for invoking the reviewer.

    Can be called with either a prompt or diff context:
    - With prompt: Returns raw InvocationResult
    - With diff: Returns structured ReviewOutput

    Args:
        prompt: The review prompt
        diff: Git diff to review (uses review() method)
        changed_files: List of changed files
        working_dir: Working directory for the command
        agents_dir: Directory containing agent definitions
        timeout: Timeout in seconds

    Returns:
        InvocationResult (for prompt) or ReviewOutput (for diff)

    Example:
        >>> # With prompt
        >>> result = invoke_reviewer("Review the auth module")
        >>> print(result.output)

        >>> # With diff
        >>> output = invoke_reviewer(diff="...", changed_files=["auth.py"])
        >>> for item in output.items:
        ...     print(item.message)
    """
    reviewer = ReviewerAgent(
        agents_dir=agents_dir or Path(DEFAULT_AGENTS_DIR),
        working_dir=working_dir,
        timeout_seconds=timeout,
    )

    if diff is not None:
        return reviewer.review(
            diff=diff,
            changed_files=changed_files,
        )

    if prompt:
        return reviewer.invoke(prompt)

    raise ValueError("Either prompt or diff must be provided")
