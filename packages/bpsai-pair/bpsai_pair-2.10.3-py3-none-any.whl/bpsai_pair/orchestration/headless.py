"""
Headless mode integration for Claude Code.

Provides programmatic invocation of Claude Code without interactive prompts,
enabling multi-agent orchestration and automated workflows.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class HeadlessResponse:
    """Structured response from a headless Claude Code invocation."""

    session_id: Optional[str] = None
    result: str = ""
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    is_error: bool = False
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    raw_output: str = ""

    @property
    def total_tokens(self) -> int:
        """Total tokens used in this invocation."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "result": self.result,
            "cost_usd": self.cost_usd,
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            },
            "is_error": self.is_error,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
        }


PermissionMode = Literal["auto", "plan", "full"]


@dataclass
class HeadlessSession:
    """
    Manages headless Claude Code sessions.

    Provides methods for invoking Claude Code programmatically,
    resuming sessions, and managing session lifecycle.

    Example:
        >>> session = HeadlessSession(permission_mode='plan')
        >>> response = session.invoke("Design an authentication system")
        >>> print(response.result)
        >>> # Continue the conversation
        >>> follow_up = session.resume("Add OAuth support")
    """

    permission_mode: PermissionMode = "auto"
    working_dir: Optional[Path] = None
    timeout_seconds: int = 300
    session_id: Optional[str] = None
    _invocation_count: int = field(default=0, repr=False)
    _total_cost: float = field(default=0.0, repr=False)
    _total_tokens: int = field(default=0, repr=False)

    def invoke(self, prompt: str) -> HeadlessResponse:
        """
        Send a prompt to Claude Code in headless mode.

        Args:
            prompt: The prompt to send

        Returns:
            HeadlessResponse with result and metadata
        """
        return self._execute(prompt, resume=False)

    def resume(self, prompt: str) -> HeadlessResponse:
        """
        Continue an existing session with a follow-up prompt.

        Args:
            prompt: The follow-up prompt

        Returns:
            HeadlessResponse with result and metadata

        Raises:
            ValueError: If no session exists to resume
        """
        if not self.session_id:
            raise ValueError("No session to resume. Call invoke() first.")
        return self._execute(prompt, resume=True)

    def terminate(self) -> None:
        """Clean up the session."""
        self.session_id = None
        logger.info(
            f"Session terminated. Total cost: ${self._total_cost:.4f}, "
            f"Total tokens: {self._total_tokens}"
        )

    @staticmethod
    def _check_budget(prompt: str, start_time: float) -> Optional[HeadlessResponse]:
        """
        Check budget before expensive AI operation.

        Returns:
            HeadlessResponse with error if over budget, None if OK to proceed.
        """
        try:
            from ..metrics.budget import BudgetEnforcer
            from ..metrics.collector import MetricsCollector
            from ..tokens import estimate_prompt_tokens
            from ..core.ops import find_paircoder_dir
        except ImportError:
            # Budget modules not available, skip check
            BudgetEnforcer = None  # noqa: F841
            MetricsCollector = None  # noqa: F841
            estimate_prompt_tokens = None  # noqa: F841
            find_paircoder_dir = None  # noqa: F841
            logger.debug("Budget enforcement not available, proceeding")
            return None

        try:
            history_dir = find_paircoder_dir() / "history"
            collector = MetricsCollector(history_dir)
            enforcer = BudgetEnforcer(collector)
            estimated_tokens = estimate_prompt_tokens(prompt)
            can_proceed, reason = enforcer.can_proceed(estimated_tokens)

            if not can_proceed:
                logger.warning(f"Budget exceeded: {reason}")
                return HeadlessResponse(
                    is_error=True,
                    error_message=f"Budget exceeded: {reason}",
                    duration_seconds=time.time() - start_time,
                )
        except Exception as e:
            # Log but don't block on budget check errors
            logger.warning(f"Budget check failed: {e}, proceeding anyway")

        return None  # OK to proceed

    def _execute(self, prompt: str, resume: bool = False) -> HeadlessResponse:
        """Execute a Claude Code command."""
        start_time = time.time()

        # Budget enforcement gate
        budget_error = HeadlessSession._check_budget(prompt, start_time)
        if budget_error:
            return budget_error

        cmd = self._build_command(prompt, resume)
        logger.debug(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir or Path.cwd(),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            response = self._parse_response(result.stdout, result.stderr, result.returncode)
            response.duration_seconds = time.time() - start_time
            response.raw_output = result.stdout

            # Update session state
            if response.session_id:
                self.session_id = response.session_id
            self._invocation_count += 1
            self._total_cost += response.cost_usd
            self._total_tokens += response.total_tokens

            logger.info(
                f"Invocation {self._invocation_count}: "
                f"{response.total_tokens} tokens, ${response.cost_usd:.4f}"
            )

            return response

        except subprocess.TimeoutExpired:
            return HeadlessResponse(
                is_error=True,
                error_message=f"Command timed out after {self.timeout_seconds}s",
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            return HeadlessResponse(
                is_error=True,
                error_message=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _build_command(self, prompt: str, resume: bool) -> list[str]:
        """Build the Claude Code command."""
        cmd = ["claude", "-p", prompt, "--output-format", "json"]

        # Add permission mode
        if self.permission_mode != "auto":
            cmd.extend(["--permission-mode", self.permission_mode])

        # Add resume flag if continuing session
        if resume and self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Add no-input flag for true headless operation
        cmd.append("--no-input")

        return cmd

    @staticmethod
    def _parse_response(
        stdout: str, stderr: str, returncode: int
    ) -> HeadlessResponse:
        """Parse Claude Code JSON output into HeadlessResponse."""
        if returncode != 0:
            return HeadlessResponse(
                is_error=True,
                error_message=stderr or f"Command failed with code {returncode}",
                raw_output=stdout,
            )

        try:
            # Try to parse as JSON
            data = json.loads(stdout)

            return HeadlessResponse(
                session_id=data.get("session_id"),
                result=data.get("result", ""),
                cost_usd=data.get("cost_usd", 0.0),
                input_tokens=data.get("tokens", {}).get("input", 0),
                output_tokens=data.get("tokens", {}).get("output", 0),
                is_error=data.get("is_error", False),
                error_message=data.get("error") if data.get("is_error") else None,
            )

        except json.JSONDecodeError:
            # If not JSON, treat stdout as the result
            # This handles cases where Claude outputs plain text
            return HeadlessResponse(
                result=stdout.strip(),
                is_error=False,
            )

    @property
    def stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return {
            "invocation_count": self._invocation_count,
            "total_cost_usd": self._total_cost,
            "total_tokens": self._total_tokens,
            "session_id": self.session_id,
            "permission_mode": self.permission_mode,
        }


def invoke_headless(
    prompt: str,
    permission_mode: PermissionMode = "auto",
    working_dir: Optional[Path] = None,
    timeout: int = 300,
) -> HeadlessResponse:
    """
    One-shot headless invocation of Claude Code.

    Convenience function for simple, single-prompt invocations.

    Args:
        prompt: The prompt to send
        permission_mode: Permission level ('auto', 'plan', 'full')
        working_dir: Working directory for the command
        timeout: Timeout in seconds

    Returns:
        HeadlessResponse with result and metadata

    Example:
        >>> response = invoke_headless(
        ...     "List all Python files in this project",
        ...     permission_mode='plan'
        ... )
        >>> print(response.result)
    """
    session = HeadlessSession(
        permission_mode=permission_mode,
        working_dir=working_dir,
        timeout_seconds=timeout,
    )
    return session.invoke(prompt)
