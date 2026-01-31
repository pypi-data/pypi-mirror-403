"""
Planner Agent Implementation.

Provides the PlannerAgent class for design and planning tasks.
The planner operates in read-only mode (permissionMode: plan) and
returns structured plan output.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from .invoker import AgentDefinition, AgentInvoker, InvocationResult

logger = logging.getLogger(__name__)

# Default location for agent definitions
DEFAULT_AGENTS_DIR = ".claude/agents"


@dataclass
class PlanPhase:
    """
    A phase in the implementation plan.

    Each phase represents a logical grouping of related tasks
    with associated files and activities.
    """

    name: str
    description: str
    files: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "files": self.files,
            "tasks": self.tasks,
        }


@dataclass
class PlanOutput:
    """
    Structured output from the planner agent.

    Contains the plan summary, phases, files to modify,
    complexity estimate, and identified risks.
    """

    summary: str
    phases: list[PlanPhase]
    files_to_modify: list[str]
    estimated_complexity: Literal["low", "medium", "high"]
    risks: list[str] = field(default_factory=list)
    raw_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "summary": self.summary,
            "phases": [p.to_dict() for p in self.phases],
            "files_to_modify": self.files_to_modify,
            "estimated_complexity": self.estimated_complexity,
            "risks": self.risks,
        }

    @classmethod
    def from_raw_text(cls, raw_text: str) -> "PlanOutput":
        """
        Parse plan from raw markdown output.

        Attempts to extract structured information from the planner's
        markdown-formatted response.

        Args:
            raw_text: Raw markdown text from planner output

        Returns:
            PlanOutput with parsed content
        """
        # Extract summary
        summary = ""
        summary_match = re.search(r"##\s*Summary\s*\n(.*?)(?=\n##|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
        else:
            # Use first paragraph as summary
            lines = raw_text.strip().split("\n")
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    summary = line.strip()
                    break

        # Extract phases
        phases = []
        # Match ## Phases until next ## that is not ### (e.g., ## Files but not ### Phase)
        phases_match = re.search(r"##\s*Phases?\s*\n(.*?)(?=\n##[^#]|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if phases_match:
            phases_text = phases_match.group(1)
            # Split on ### Phase N: pattern to get individual phases
            phase_splits = re.split(r"###\s*Phase\s*\d*:?\s*", phases_text, flags=re.IGNORECASE)
            for phase_block in phase_splits:
                if not phase_block.strip():
                    continue
                lines = phase_block.strip().split("\n")
                if not lines:
                    continue

                # First line is the phase name
                phase_name = lines[0].strip()
                phase_content = "\n".join(lines[1:]) if len(lines) > 1 else ""

                # Extract tasks from bullet points
                tasks = []
                for line in phase_content.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        task = line.lstrip("-*").strip()
                        if task:
                            tasks.append(task)

                phases.append(PlanPhase(
                    name=phase_name,
                    description=phase_content.split("\n")[0].strip() if phase_content else "",
                    files=[],
                    tasks=tasks,
                ))

        # Extract files to modify
        files_to_modify = []
        files_match = re.search(r"##\s*Files?\s*(?:to\s*)?(?:Modify|Change)?\s*\n(.*?)(?=\n##|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if files_match:
            files_text = files_match.group(1)
            for line in files_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    # Extract file path, handling annotations like "(new)"
                    file_path = line.lstrip("-*").strip()
                    file_path = re.sub(r"\s*\(.*?\)\s*$", "", file_path).strip()
                    if file_path and not file_path.startswith("#"):
                        files_to_modify.append(file_path)

        # Extract complexity
        complexity: Literal["low", "medium", "high"] = "medium"
        complexity_match = re.search(r"##\s*Complexity\s*\n\s*(low|medium|high)", raw_text, re.IGNORECASE)
        if complexity_match:
            complexity = complexity_match.group(1).lower()  # type: ignore

        # Extract risks
        risks = []
        risks_match = re.search(r"##\s*Risks?\s*\n(.*?)(?=\n##|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
        if risks_match:
            risks_text = risks_match.group(1)
            for line in risks_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    risk = line.lstrip("-*").strip()
                    if risk:
                        risks.append(risk)

        return cls(
            summary=summary,
            phases=phases,
            files_to_modify=files_to_modify,
            estimated_complexity=complexity,
            risks=risks,
            raw_output=raw_text,
        )


@dataclass
class PlannerAgent:
    """
    Planner agent for design and planning tasks.

    Uses the AgentInvoker framework to invoke the planner agent
    defined in .claude/agents/planner.md. Always operates in
    read-only 'plan' permission mode.

    Example:
        >>> planner = PlannerAgent()
        >>> result = planner.invoke("Design an authentication system")
        >>> print(result.output)

        >>> # Or get structured plan output
        >>> plan = planner.plan(task_id="TASK-001")
        >>> for phase in plan.phases:
        ...     print(f"{phase.name}: {phase.description}")
    """

    agents_dir: Path = field(default_factory=lambda: Path(DEFAULT_AGENTS_DIR))
    working_dir: Optional[Path] = None
    timeout_seconds: int = 300
    agent_name: str = "planner"
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
        Load the planner agent definition.

        Returns:
            AgentDefinition for the planner agent
        """
        if self._agent_definition is None:
            self._agent_definition = self._get_invoker().load_agent(self.agent_name)
        return self._agent_definition

    def build_context(
        self,
        task_id: str,
        task_dir: Optional[Path] = None,
        context_dir: Optional[Path] = None,
        relevant_files: Optional[list[Path]] = None,
    ) -> str:
        """
        Build context string for planner invocation.

        Combines task description, project context, and relevant
        source files into a comprehensive context string.

        Args:
            task_id: ID of the task to plan
            task_dir: Directory containing task files
            context_dir: Directory containing context files (state.md, project.md)
            relevant_files: Optional list of relevant source files

        Returns:
            Combined context string
        """
        context_parts = []

        # Add task content
        if task_dir:
            task_file = task_dir / "tasks" / f"{task_id}.task.md"
            if task_file.exists():
                context_parts.append(f"## Task\n\n{task_file.read_text(encoding='utf-8')}")
            else:
                # Try alternate naming patterns
                for pattern in [f"{task_id}*.md", f"*{task_id}*.md"]:
                    for f in (task_dir / "tasks").glob(pattern):
                        context_parts.append(f"## Task\n\n{f.read_text(encoding='utf-8')}")
                        break

        # Add project context
        if context_dir:
            project_file = context_dir / "project.md"
            if project_file.exists():
                context_parts.append(f"## Project Context\n\n{project_file.read_text(encoding='utf-8')}")

            state_file = context_dir / "state.md"
            if state_file.exists():
                context_parts.append(f"## Current State\n\n{state_file.read_text(encoding='utf-8')}")

        # Add relevant source files
        if relevant_files:
            for file_path in relevant_files:
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    rel_path = file_path.relative_to(self.working_dir) if self.working_dir else file_path
                    context_parts.append(f"## Source: {rel_path}\n\n```\n{content}\n```")

        return "\n\n---\n\n".join(context_parts) if context_parts else f"Plan task: {task_id}"

    def invoke(self, prompt: str, **kwargs) -> InvocationResult:
        """
        Invoke the planner agent with a prompt.

        Args:
            prompt: The planning prompt/task description
            **kwargs: Additional arguments for the invoker

        Returns:
            InvocationResult with output and metadata
        """
        invoker = self._get_invoker()
        return invoker.invoke(self.agent_name, prompt, **kwargs)

    def plan(
        self,
        task_id: str,
        task_dir: Optional[Path] = None,
        context_dir: Optional[Path] = None,
        relevant_files: Optional[list[Path]] = None,
    ) -> PlanOutput:
        """
        Generate a structured plan for a task.

        Builds comprehensive context, invokes the planner agent,
        and parses the output into a structured PlanOutput.

        Args:
            task_id: ID of the task to plan
            task_dir: Directory containing task files
            context_dir: Directory containing context files
            relevant_files: Optional list of relevant source files

        Returns:
            PlanOutput with structured plan
        """
        # Build context
        context = self.build_context(
            task_id=task_id,
            task_dir=task_dir,
            context_dir=context_dir,
            relevant_files=relevant_files,
        )

        # Add planning instructions
        planning_prompt = f"""Please analyze the following task and create a detailed implementation plan.

Your plan should include:
1. A brief summary of what needs to be done
2. Phased breakdown with specific tasks
3. List of files that need to be modified or created
4. Complexity assessment (low/medium/high)
5. Risks and mitigations

Format your response with these sections:
- ## Summary
- ## Phases (with ### Phase N: Name subsections)
- ## Files to Modify
- ## Complexity
- ## Risks

---

{context}"""

        # Invoke planner
        result = self.invoke(planning_prompt)

        if not result.success:
            logger.error(f"Planner invocation failed: {result.error}")
            return PlanOutput(
                summary=f"Planning failed: {result.error}",
                phases=[],
                files_to_modify=[],
                estimated_complexity="medium",
                risks=["Planning failed - manual review required"],
                raw_output="",
            )

        # Parse output
        return PlanOutput.from_raw_text(result.output)


def should_trigger_planner(
    task_type: Optional[str] = None,
    task_title: Optional[str] = None,
    explicit_request: bool = False,
) -> bool:
    """
    Determine if the planner agent should be triggered.

    Trigger conditions:
    - Task type is DESIGN
    - Task title contains "plan", "design", or "architecture"
    - User explicitly requests planning

    Args:
        task_type: Type of the task (DESIGN, IMPLEMENT, etc.)
        task_title: Title of the task
        explicit_request: Whether user explicitly requested planning

    Returns:
        True if planner should be triggered
    """
    if explicit_request:
        return True

    if task_type and task_type.upper() == "DESIGN":
        return True

    if task_title:
        title_lower = task_title.lower()
        trigger_words = ["plan", "design", "architecture"]
        if any(word in title_lower for word in trigger_words):
            return True

    return False


def invoke_planner(
    prompt: Optional[str] = None,
    task_id: Optional[str] = None,
    working_dir: Optional[Path] = None,
    agents_dir: Optional[Path] = None,
    timeout: int = 300,
) -> InvocationResult | PlanOutput:
    """
    Convenience function for invoking the planner.

    Can be called with either a prompt or a task_id:
    - With prompt: Returns raw InvocationResult
    - With task_id: Returns structured PlanOutput

    Args:
        prompt: The planning prompt
        task_id: Task ID to plan (uses plan() method)
        working_dir: Working directory for the command
        agents_dir: Directory containing agent definitions
        timeout: Timeout in seconds

    Returns:
        InvocationResult (for prompt) or PlanOutput (for task_id)

    Example:
        >>> # With prompt
        >>> result = invoke_planner("Design an authentication system")
        >>> print(result.output)

        >>> # With task ID
        >>> plan = invoke_planner(task_id="TASK-001")
        >>> for phase in plan.phases:
        ...     print(phase.name)
    """
    planner = PlannerAgent(
        agents_dir=agents_dir or Path(DEFAULT_AGENTS_DIR),
        working_dir=working_dir,
        timeout_seconds=timeout,
    )

    if task_id:
        from ..core.ops import find_paircoder_dir
        task_dir = (working_dir / ".paircoder") if working_dir else find_paircoder_dir()
        context_dir = task_dir / "context"
        return planner.plan(
            task_id=task_id,
            task_dir=task_dir,
            context_dir=context_dir,
        )

    if prompt:
        return planner.invoke(prompt)

    raise ValueError("Either prompt or task_id must be provided")
