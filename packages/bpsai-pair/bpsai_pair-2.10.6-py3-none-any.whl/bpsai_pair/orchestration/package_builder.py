"""
Handoff package data structures for agent context transfer.

This module contains the core data structures for packaging context
when handing off work between AI coding agents.

Classes:
    HandoffPackage: Basic handoff data structure
    EnhancedHandoffPackage: Extended structure with chain tracking
    HandoffChain: Track sequence of handoffs for debugging

Functions:
    generate_handoff_id: Generate a unique handoff identifier

Extracted from handoff.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

# Agent type literal for type checking
AgentType = Literal["claude", "codex", "cursor", "generic"]


def generate_handoff_id() -> str:
    """Generate a unique handoff ID.

    Returns:
        A unique identifier in the format 'handoff-{8 hex chars}'
    """
    return f"handoff-{uuid.uuid4().hex[:8]}"


@dataclass
class HandoffPackage:
    """Represents a packaged context bundle for agent handoff.

    This is the basic handoff structure used for simple agent transfers.
    For more complex scenarios with chain tracking, use EnhancedHandoffPackage.

    Attributes:
        task_id: Identifier for the task being handed off
        source_agent: The agent type creating the handoff
        target_agent: The agent type receiving the handoff
        created_at: When the handoff was created (defaults to now)
        token_estimate: Estimated token count for the context
        files_included: List of file paths included in the handoff
        conversation_summary: Summary of prior conversation context
        task_description: Description of the task to complete
        current_state: Current state of the work
        instructions: Specific instructions for the receiving agent
    """

    task_id: str
    source_agent: AgentType
    target_agent: AgentType
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    token_estimate: int = 0
    files_included: list[str] = field(default_factory=list)
    conversation_summary: str = ""
    task_description: str = ""
    current_state: str = ""
    instructions: str = ""

    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata dictionary for JSON serialization.

        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "version": "1.0",
            "task_id": self.task_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "created_at": self.created_at.isoformat(),
            "token_estimate": self.token_estimate,
            "files_included": self.files_included,
            "conversation_summary": self.conversation_summary,
        }

    def generate_handoff_md(self) -> str:
        """Generate HANDOFF.md content for the receiving agent.

        Returns:
            Markdown-formatted handoff document
        """
        return f"""# Agent Handoff: {self.task_id}

> **From:** {self.source_agent}
> **To:** {self.target_agent}
> **Created:** {self.created_at.strftime('%Y-%m-%d %H:%M UTC')}

## Task

{self.task_description}

## Current State

{self.current_state}

## Key Files

{self._format_files_list()}

## Instructions

{self.instructions}

## Constraints

- **Token budget:** ~{self.token_estimate} tokens
- **Scope:** Complete the specific task described above
- **Do not:** Make changes outside the scope of this task

## Conversation Summary

{self.conversation_summary or "No prior conversation context."}
"""

    def _format_files_list(self) -> str:
        """Format the files list for markdown.

        Returns:
            Markdown-formatted file list or placeholder text
        """
        if not self.files_included:
            return "No specific files included."
        return "\n".join(f"- `{f}`" for f in self.files_included)


@dataclass
class EnhancedHandoffPackage:
    """
    Enhanced handoff package with structured context for agent transfers.

    Extends the basic HandoffPackage with:
    - Acceptance criteria tracking
    - Work completed/remaining state
    - Chain tracking for debugging multi-hop handoffs
    - Token budget estimation
    - Optional inline file contents

    Attributes:
        task_id: ID of the task being handed off
        source_agent: Name of the agent creating the handoff
        target_agent: Name of the agent receiving the handoff
        task_description: Description of the task
        acceptance_criteria: List of acceptance criteria to verify
        files_touched: List of file paths involved
        current_state: Current state of the work
        work_completed: Summary of completed work
        remaining_work: Summary of remaining work
        token_budget: Estimated token budget for the task
        handoff_id: Unique identifier for this handoff
        previous_handoff_id: ID of previous handoff in chain
        chain_depth: Number of prior handoffs in chain
        created_at: When the handoff was created
        file_contents: Optional dict of file path to content

    Example:
        >>> package = EnhancedHandoffPackage(
        ...     task_id="TASK-001",
        ...     source_agent="planner",
        ...     target_agent="reviewer",
        ...     task_description="Review auth implementation",
        ...     work_completed="Basic auth done",
        ...     remaining_work="OAuth support needed",
        ... )
        >>> context = package.generate_context_markdown()
    """

    # Required fields
    task_id: str
    source_agent: str
    target_agent: str

    # Task context
    task_description: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)

    # State tracking
    current_state: str = ""
    work_completed: str = ""
    remaining_work: str = ""

    # Resource planning
    token_budget: int = 0

    # Chain tracking
    handoff_id: str = field(default_factory=generate_handoff_id)
    previous_handoff_id: Optional[str] = None
    chain_depth: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional file contents (for inline handoff)
    file_contents: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "version": "2.0",
            "task_id": self.task_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "task_description": self.task_description,
            "acceptance_criteria": self.acceptance_criteria,
            "files_touched": self.files_touched,
            "current_state": self.current_state,
            "work_completed": self.work_completed,
            "remaining_work": self.remaining_work,
            "token_budget": self.token_budget,
            "handoff_id": self.handoff_id,
            "previous_handoff_id": self.previous_handoff_id,
            "chain_depth": self.chain_depth,
            "created_at": self.created_at.isoformat(),
            "file_contents": self.file_contents,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnhancedHandoffPackage":
        """Create from dictionary.

        Args:
            data: Dictionary with package data

        Returns:
            New EnhancedHandoffPackage instance
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            task_id=data["task_id"],
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            task_description=data.get("task_description", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            files_touched=data.get("files_touched", []),
            current_state=data.get("current_state", ""),
            work_completed=data.get("work_completed", ""),
            remaining_work=data.get("remaining_work", ""),
            token_budget=data.get("token_budget", 0),
            handoff_id=data.get("handoff_id", generate_handoff_id()),
            previous_handoff_id=data.get("previous_handoff_id"),
            chain_depth=data.get("chain_depth", 0),
            created_at=created_at,
            file_contents=data.get("file_contents", {}),
        )

    def generate_context_markdown(self) -> str:
        """
        Generate markdown context for the receiving agent.

        Creates a comprehensive handoff document that includes
        task details, acceptance criteria, work status, and
        chain information for debugging.

        Returns:
            Markdown-formatted context document
        """
        ac_list = "\n".join(f"- {ac}" for ac in self.acceptance_criteria) or "- None specified"
        files_list = "\n".join(f"- `{f}`" for f in self.files_touched) or "- No files tracked"

        chain_info = f"**Chain Depth:** {self.chain_depth}"
        if self.previous_handoff_id:
            chain_info += f"\n**Previous Handoff:** {self.previous_handoff_id}"

        file_contents_section = ""
        if self.file_contents:
            file_contents_section = "\n## File Contents\n\n"
            for path, content in self.file_contents.items():
                ext = Path(path).suffix.lstrip(".")
                file_contents_section += f"### `{path}`\n\n```{ext}\n{content}\n```\n\n"

        return f"""# Agent Handoff: {self.task_id}

> **Handoff ID:** {self.handoff_id}
> **From:** {self.source_agent}
> **To:** {self.target_agent}
> **Created:** {self.created_at.strftime('%Y-%m-%d %H:%M UTC')}

## Task Description

{self.task_description or "No description provided."}

## Acceptance Criteria

{ac_list}

## Current State

{self.current_state or "Not specified."}

## Work Completed

{self.work_completed or "No work completed yet."}

## Remaining Work

{self.remaining_work or "Not specified."}

## Files Touched

{files_list}

## Chain Information

{chain_info}

## Constraints

- **Token budget:** ~{self.token_budget} tokens
- **Scope:** Complete the specific task described above
- **Do not:** Make changes outside the scope of this task
{file_contents_section}"""


@dataclass
class HandoffChain:
    """
    Tracks a sequence of handoffs for a task.

    Useful for debugging multi-agent workflows and understanding
    how context flows between agents.

    Attributes:
        task_id: The task these handoffs are for
        handoffs: List of handoff packages in order
        created_at: When the chain was created

    Example:
        >>> chain = HandoffChain(task_id="TASK-001")
        >>> chain.add(handoff1)
        >>> chain.add(handoff2)
        >>> print(chain.get_history())
    """

    task_id: str
    handoffs: list[EnhancedHandoffPackage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_depth(self) -> int:
        """Get the current chain depth.

        Returns:
            Number of handoffs in the chain
        """
        return len(self.handoffs)

    def add(self, package: EnhancedHandoffPackage) -> None:
        """Add a handoff to the chain.

        Args:
            package: The handoff package to add
        """
        self.handoffs.append(package)

    def get_history(self) -> list[dict[str, Any]]:
        """Get the handoff history as a list of summaries.

        Returns:
            List of dictionaries with handoff summaries
        """
        return [
            {
                "handoff_id": h.handoff_id,
                "source_agent": h.source_agent,
                "target_agent": h.target_agent,
                "work_completed": h.work_completed,
                "created_at": h.created_at.isoformat(),
            }
            for h in self.handoffs
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON
        """
        return {
            "task_id": self.task_id,
            "handoffs": [h.to_dict() for h in self.handoffs],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandoffChain":
        """Create from dictionary.

        Args:
            data: Dictionary with chain data

        Returns:
            New HandoffChain instance
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        chain = cls(
            task_id=data["task_id"],
            created_at=created_at,
        )
        for h_data in data.get("handoffs", []):
            chain.handoffs.append(EnhancedHandoffPackage.from_dict(h_data))

        return chain
