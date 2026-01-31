"""
Agent handoff protocol for context transfer between AI coding agents.

Provides packaging and unpacking of context bundles for seamless
task delegation across agent boundaries (Claude, Codex, Cursor, etc.).

This module is the hub that re-exports from decomposed modules:
- package_builder: Data structures (HandoffPackage, EnhancedHandoffPackage, HandoffChain)
- serializer: Persistence (HandoffSerializer)
- manager: Pack/unpack operations (HandoffManager)

Public API:
- HandoffPackage: Basic handoff data structure
- EnhancedHandoffPackage: Extended structure with chain tracking
- HandoffChain: Track sequence of handoffs for debugging
- HandoffSerializer: Save/load handoffs to disk
- HandoffManager: Pack/unpack handoff tarballs
- prepare_handoff(): Create handoff from current state
- receive_handoff(): Receive and parse handoff from another agent

Decomposed in Sprint 29.6 (EPIC-005 Phase 3).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

# Re-export data structures from package_builder
from .package_builder import (
    AgentType,
    HandoffPackage,
    EnhancedHandoffPackage,
    HandoffChain,
    generate_handoff_id as _generate_handoff_id,
)

# Re-export serializer
from .serializer import HandoffSerializer

# Re-export manager
from .manager import HandoffManager

logger = logging.getLogger(__name__)

# Backwards compatibility alias
_generate_handoff_id = _generate_handoff_id


def prepare_handoff(
    task_id: str,
    source_agent: str,
    target_agent: str,
    task_description: str = "",
    acceptance_criteria: Optional[list[str]] = None,
    files_touched: Optional[list[str]] = None,
    current_state: str = "",
    work_completed: str = "",
    remaining_work: str = "",
    previous_handoff_id: Optional[str] = None,
    working_dir: Optional[Path] = None,
    include_file_contents: bool = False,
    save: bool = False,
    handoffs_dir: Optional[Path] = None,
) -> EnhancedHandoffPackage:
    """
    Prepare a handoff package for transferring context to another agent.

    This function creates a structured handoff package that captures:
    - Task context and acceptance criteria
    - Work completed and remaining
    - Files involved
    - Chain tracking information

    Args:
        task_id: ID of the task being handed off
        source_agent: Name of the agent creating the handoff
        target_agent: Name of the agent receiving the handoff
        task_description: Description of the task
        acceptance_criteria: List of acceptance criteria
        files_touched: List of file paths involved
        current_state: Current state of the work
        work_completed: Summary of completed work
        remaining_work: Summary of remaining work
        previous_handoff_id: ID of previous handoff in chain
        working_dir: Working directory for file operations
        include_file_contents: Whether to include file contents inline
        save: Whether to save the handoff to disk
        handoffs_dir: Directory for saving handoffs

    Returns:
        EnhancedHandoffPackage ready for transfer

    Example:
        >>> package = prepare_handoff(
        ...     task_id="TASK-001",
        ...     source_agent="planner",
        ...     target_agent="reviewer",
        ...     task_description="Review auth implementation",
        ...     work_completed="OAuth2 support added",
        ...     remaining_work="Code review needed",
        ... )
    """
    working_dir = working_dir or Path.cwd()
    acceptance_criteria = acceptance_criteria or []
    files_touched = files_touched or []

    # Calculate chain depth
    chain_depth = 0
    if previous_handoff_id:
        try:
            serializer = HandoffSerializer(handoffs_dir=handoffs_dir)
            prev = serializer.load(previous_handoff_id)
            chain_depth = prev.chain_depth + 1
        except FileNotFoundError:
            chain_depth = 1

    # Estimate token budget
    token_budget = 0
    file_contents: dict[str, str] = {}

    if files_touched:
        for file_path in files_touched:
            full_path = working_dir / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    # Estimate ~4 chars per token
                    token_budget += len(content) // 4

                    if include_file_contents:
                        file_contents[file_path] = content
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

    # Add overhead for context
    token_budget += 500  # Base overhead

    package = EnhancedHandoffPackage(
        task_id=task_id,
        source_agent=source_agent,
        target_agent=target_agent,
        task_description=task_description,
        acceptance_criteria=acceptance_criteria,
        files_touched=files_touched,
        current_state=current_state,
        work_completed=work_completed,
        remaining_work=remaining_work,
        token_budget=token_budget,
        previous_handoff_id=previous_handoff_id,
        chain_depth=chain_depth,
        file_contents=file_contents,
    )

    if save:
        serializer = HandoffSerializer(handoffs_dir=handoffs_dir)
        serializer.save(package)

        # Update chain
        chain = serializer.load_chain(task_id)
        chain.add(package)
        serializer.save_chain(chain)

    return package


def receive_handoff(
    handoff_id: str,
    handoffs_dir: Optional[Path] = None,
    generate_context: bool = False,
) -> Union[EnhancedHandoffPackage, Tuple[EnhancedHandoffPackage, str]]:
    """
    Receive and parse a handoff from another agent.

    Args:
        handoff_id: ID of the handoff to receive
        handoffs_dir: Directory containing handoff files
        generate_context: Whether to generate context markdown

    Returns:
        If generate_context is False: EnhancedHandoffPackage
        If generate_context is True: Tuple of (package, context_markdown)

    Raises:
        FileNotFoundError: If handoff doesn't exist

    Example:
        >>> package, context = receive_handoff(
        ...     "handoff-abc123",
        ...     generate_context=True,
        ... )
        >>> print(context)  # Ready for agent consumption
    """
    serializer = HandoffSerializer(handoffs_dir=handoffs_dir)
    package = serializer.load(handoff_id)

    if generate_context:
        context = package.generate_context_markdown()
        return package, context

    return package


# Public API
__all__ = [
    # Types
    "AgentType",
    # Data structures
    "HandoffPackage",
    "EnhancedHandoffPackage",
    "HandoffChain",
    # Classes
    "HandoffSerializer",
    "HandoffManager",
    # Functions
    "prepare_handoff",
    "receive_handoff",
]
