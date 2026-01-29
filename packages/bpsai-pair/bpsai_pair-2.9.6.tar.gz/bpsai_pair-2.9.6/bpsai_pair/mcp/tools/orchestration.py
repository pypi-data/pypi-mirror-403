"""
MCP Orchestration Tools

Implements orchestration tools:
- paircoder_orchestrate_analyze: Analyze task and get model recommendation
- paircoder_orchestrate_handoff: Create handoff package for agent transitions
- paircoder_orchestrate_plan: Invoke planner agent for design tasks
- paircoder_orchestrate_review: Invoke reviewer agent for code review
"""

from pathlib import Path
from typing import Any, Optional


def find_paircoder_dir() -> Path:
    """Find the .paircoder directory."""
    from ...core.ops import find_paircoder_dir as _find_paircoder_dir, ProjectRootNotFoundError
    try:
        paircoder_dir = _find_paircoder_dir()
    except ProjectRootNotFoundError:
        raise FileNotFoundError("No .paircoder directory found")
    if not paircoder_dir.exists():
        raise FileNotFoundError("No .paircoder directory found")
    return paircoder_dir


def get_project_root() -> Path:
    """Get the project root (parent of .paircoder)."""
    from ...core.ops import find_project_root, ProjectRootNotFoundError
    try:
        return find_project_root()
    except ProjectRootNotFoundError:
        raise FileNotFoundError("No project root found")


def register_orchestration_tools(server: Any) -> None:
    """Register orchestration tools with the MCP server."""

    @server.tool()
    async def paircoder_orchestrate_analyze(
        task_id: str,
        context: Optional[str] = None,
        prefer_agent: Optional[str] = None,
    ) -> dict:
        """
        Analyze task complexity and recommend model/agent.

        Args:
            task_id: Task ID to analyze
            context: Additional context for analysis (optional)
            prefer_agent: Preferred agent override (optional)

        Returns:
            Analysis with complexity, recommended model, and reasoning
        """
        try:
            from ...orchestration import Orchestrator

            project_root = get_project_root()
            orchestrator = Orchestrator(project_root=project_root)

            # Analyze task
            task = orchestrator.analyze_task(task_id)

            # Get routing decision
            constraints = {}
            if prefer_agent:
                constraints["prefer"] = prefer_agent

            decision = orchestrator.select_agent(task, constraints)

            # Map complexity to band
            complexity_bands = {
                "low": "trivial",
                "medium": "moderate",
                "high": "complex",
            }

            # Estimate tokens and cost
            estimated_tokens = task.estimated_tokens
            agent_caps = orchestrator.agents.get(decision.agent)
            cost_per_token = (agent_caps.cost_per_1k_tokens / 1000) if agent_caps else 0.015

            return {
                "task_id": task_id,
                "task_type": task.task_type.value,
                "complexity_score": decision.score,
                "complexity_band": complexity_bands.get(task.complexity.value, "moderate"),
                "scope": task.scope.value,
                "recommended_agent": decision.agent,
                "reasoning": decision.reasoning,
                "requires_reasoning": task.requires_reasoning,
                "requires_iteration": task.requires_iteration,
                "estimated_tokens": estimated_tokens,
                "estimated_cost": f"${estimated_tokens * cost_per_token:.2f}",
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_orchestrate_handoff(
        task_id: str,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        progress_summary: str = "",
        files_in_progress: Optional[list] = None,
        decisions_made: Optional[list] = None,
        open_questions: Optional[list] = None,
    ) -> dict:
        """
        Create handoff package for agent transition.

        Args:
            task_id: Task ID being handed off
            from_agent: Source agent (optional)
            to_agent: Target agent (optional, defaults to 'codex')
            progress_summary: Summary of work done
            files_in_progress: List of files being worked on
            decisions_made: Key decisions made during work
            open_questions: Unresolved questions

        Returns:
            Handoff package metadata
        """
        try:
            from ...orchestration import HandoffManager

            project_root = get_project_root()
            manager = HandoffManager(project_root=project_root)

            # Prepare file paths
            include_files = None
            if files_in_progress:
                include_files = [project_root / f for f in files_in_progress]

            # Build summary with decisions and questions
            full_summary = progress_summary
            if decisions_made:
                full_summary += "\n\n**Decisions Made:**\n"
                for decision in decisions_made:
                    full_summary += f"- {decision}\n"
            if open_questions:
                full_summary += "\n\n**Open Questions:**\n"
                for question in open_questions:
                    full_summary += f"- {question}\n"

            # Create handoff package
            package_path = manager.pack(
                task_id=task_id,
                source_agent=from_agent or "claude",
                target_agent=to_agent or "codex",
                include_files=include_files,
                conversation_summary=full_summary,
            )

            return {
                "status": "created",
                "task_id": task_id,
                "from_agent": from_agent or "claude",
                "to_agent": to_agent or "codex",
                "package_path": str(package_path),
                "files_included": files_in_progress or [],
                "summary_length": len(full_summary),
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_orchestrate_plan(
        task_id: str,
        prompt: Optional[str] = None,
        include_files: Optional[list] = None,
    ) -> dict:
        """
        Invoke the planner agent for design and planning tasks.

        The planner operates in read-only mode and returns a structured
        implementation plan with phases, files to modify, and complexity estimates.

        Args:
            task_id: Task ID to plan (loads context from task file)
            prompt: Optional additional prompt/instructions for planning
            include_files: Optional list of relevant source files to include in context

        Returns:
            Structured plan with phases, files, complexity, and risks
        """
        try:
            from ...orchestration import PlannerAgent

            project_root = get_project_root()

            planner = PlannerAgent(
                agents_dir=project_root / ".claude" / "agents",
                working_dir=project_root,
            )

            task_dir = project_root / ".paircoder"
            context_dir = task_dir / "context"

            # Prepare relevant files
            relevant_files = None
            if include_files:
                relevant_files = [project_root / f for f in include_files]

            plan = planner.plan(
                task_id=task_id,
                task_dir=task_dir,
                context_dir=context_dir,
                relevant_files=relevant_files,
            )

            return {
                "status": "success",
                "task_id": task_id,
                "summary": plan.summary,
                "phases": [
                    {
                        "name": phase.name,
                        "description": phase.description,
                        "tasks": phase.tasks,
                        "files": phase.files,
                    }
                    for phase in plan.phases
                ],
                "files_to_modify": plan.files_to_modify,
                "complexity": plan.estimated_complexity,
                "risks": plan.risks,
                "raw_output": plan.raw_output,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_orchestrate_review(
        diff: Optional[str] = None,
        changed_files: Optional[list] = None,
        include_file_contents: bool = True,
    ) -> dict:
        """
        Invoke the reviewer agent for code review tasks.

        The reviewer operates in read-only mode and returns structured
        feedback with items categorized by severity and an overall verdict.

        Args:
            diff: Git diff to review (if not provided, uses current git diff)
            changed_files: List of changed file paths (auto-detected if not provided)
            include_file_contents: Whether to include full file contents in context

        Returns:
            Structured review with verdict, items by severity, and positive notes
        """
        import subprocess

        try:
            from ...orchestration import ReviewerAgent

            project_root = get_project_root()

            reviewer = ReviewerAgent(
                agents_dir=project_root / ".claude" / "agents",
                working_dir=project_root,
            )

            # Auto-detect diff if not provided
            if diff is None:
                try:
                    diff_result = subprocess.run(
                        ["git", "diff", "HEAD"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    diff = diff_result.stdout if diff_result.returncode == 0 else ""
                except Exception:
                    diff = ""

            # Auto-detect changed files if not provided
            if changed_files is None:
                try:
                    files_result = subprocess.run(
                        ["git", "diff", "--name-only", "HEAD"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if files_result.returncode == 0:
                        changed_files = [f for f in files_result.stdout.strip().split("\n") if f]
                    else:
                        changed_files = []
                except Exception:
                    changed_files = []

            output = reviewer.review(
                diff=diff,
                changed_files=changed_files,
                include_file_contents=include_file_contents,
            )

            return {
                "status": "success",
                "verdict": output.verdict.value,
                "summary": output.summary,
                "items": [
                    {
                        "severity": item.severity.value,
                        "file_path": item.file_path,
                        "line_number": item.line_number,
                        "message": item.message,
                        "suggestion": item.suggestion,
                    }
                    for item in output.items
                ],
                "counts": {
                    "blocker": output.blocker_count,
                    "warning": output.warning_count,
                    "info": output.info_count,
                },
                "has_blockers": output.has_blockers,
                "positive_notes": output.positive_notes,
                "raw_output": output.raw_output,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}
