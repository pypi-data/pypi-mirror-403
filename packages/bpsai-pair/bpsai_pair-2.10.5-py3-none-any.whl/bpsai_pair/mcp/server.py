"""
MCP Server Implementation

Provides the main server setup and run functionality for the PairCoder MCP server.
"""

import asyncio

from ..licensing import require_feature

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    Server = None
    stdio_server = None


@require_feature("mcp")
def create_server(name: str = "paircoder") -> "Server":
    """
    Create and configure the MCP server with all tools.

    Args:
        name: Server name

    Returns:
        Configured Server instance
    """
    if not HAS_MCP:
        raise ImportError(
            "MCP package not installed. Install with: pip install 'bpsai-pair[mcp]'"
        )

    server = Server(name)

    # Register all tools
    from .tools import (
        register_task_tools,
        register_planning_tools,
        register_context_tools,
        register_orchestration_tools,
        register_metrics_tools,
        register_trello_tools,
    )

    register_task_tools(server)
    register_planning_tools(server)
    register_context_tools(server)
    register_orchestration_tools(server)
    register_metrics_tools(server)
    register_trello_tools(server)

    return server


@require_feature("mcp")
def run_server(transport: str = "stdio", port: int = 3000) -> None:
    """
    Run the MCP server.

    Args:
        transport: Transport type (stdio or sse)
        port: Port for SSE transport
    """
    if not HAS_MCP:
        raise ImportError(
            "MCP package not installed. Install with: pip install 'bpsai-pair[mcp]'"
        )

    server = create_server()

    if transport == "stdio":
        asyncio.run(_run_stdio(server))
    elif transport == "sse":
        raise NotImplementedError("SSE transport not yet implemented")
    else:
        raise ValueError(f"Unknown transport: {transport}")


async def _run_stdio(server: "Server") -> None:
    """Run server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def list_tools() -> list[dict]:
    """
    List all available MCP tools.

    Returns:
        List of tool info dictionaries
    """
    tools = [
        {
            "name": "paircoder_task_list",
            "description": "List tasks with filters (status, plan, sprint)",
            "parameters": ["status", "plan", "sprint"],
        },
        {
            "name": "paircoder_task_next",
            "description": "Get the next recommended task to work on",
            "parameters": [],
        },
        {
            "name": "paircoder_task_start",
            "description": "Start a task - updates status and triggers hooks",
            "parameters": ["task_id", "agent"],
        },
        {
            "name": "paircoder_task_complete",
            "description": "Complete a task - updates status and triggers hooks",
            "parameters": ["task_id", "summary"],
        },
        {
            "name": "paircoder_context_read",
            "description": "Read project context files (state, project, workflow, config, capabilities)",
            "parameters": ["file"],
        },
        {
            "name": "paircoder_plan_status",
            "description": "Get plan status with sprint/task breakdown",
            "parameters": ["plan_id"],
        },
        {
            "name": "paircoder_plan_list",
            "description": "List available plans",
            "parameters": [],
        },
        {
            "name": "paircoder_orchestrate_analyze",
            "description": "Analyze task complexity and get model/agent recommendation",
            "parameters": ["task_id", "context", "prefer_agent"],
        },
        {
            "name": "paircoder_orchestrate_handoff",
            "description": "Create handoff package for agent transition",
            "parameters": ["task_id", "from_agent", "to_agent", "progress_summary"],
        },
        {
            "name": "paircoder_metrics_record",
            "description": "Record token usage and cost metrics for an action",
            "parameters": ["task_id", "agent", "model", "input_tokens", "output_tokens"],
        },
        {
            "name": "paircoder_metrics_summary",
            "description": "Get metrics summary (daily, weekly, monthly, or by task)",
            "parameters": ["scope", "scope_id"],
        },
        {
            "name": "paircoder_trello_sync_plan",
            "description": "Sync plan tasks to Trello board as cards",
            "parameters": ["plan_id", "board_id", "create_lists", "link_cards"],
        },
        {
            "name": "paircoder_trello_update_card",
            "description": "Update Trello card on task state change",
            "parameters": ["task_id", "action", "comment"],
        },
    ]
    return tools


async def test_tool(tool_name: str, input_data: dict) -> dict:
    """
    Test an MCP tool locally.

    This function works without the MCP package installed, allowing testing
    of tool logic independently.

    Args:
        tool_name: Name of the tool to test
        input_data: Tool input parameters

    Returns:
        Tool result
    """

    # Map tool names to handlers
    from bpsai_pair.mcp.tools.tasks import find_paircoder_dir
    from bpsai_pair.planning.parser import TaskParser, PlanParser
    from bpsai_pair.planning.state import StateManager
    from bpsai_pair.planning.models import TaskStatus

    paircoder_dir = find_paircoder_dir()

    if tool_name == "paircoder_task_list":
        task_parser = TaskParser(paircoder_dir / "tasks")
        status = input_data.get("status", "all")
        plan = input_data.get("plan")
        sprint = input_data.get("sprint")

        if plan:
            tasks = task_parser.get_tasks_for_plan(plan)
        else:
            tasks = task_parser.parse_all()

        if status != "all":
            try:
                status_filter = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_filter]
            except ValueError:
                pass

        if sprint:
            tasks = [t for t in tasks if t.sprint == sprint]

        return [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority,
                "sprint": t.sprint,
            }
            for t in tasks
        ]

    elif tool_name == "paircoder_task_next":
        state_manager = StateManager(paircoder_dir)
        task = state_manager.get_next_task()
        if not task:
            return {"error": {"code": "NO_TASKS", "message": "No pending tasks"}}
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority,
        }

    elif tool_name == "paircoder_task_start":
        task_id = input_data.get("task_id")
        if not task_id:
            return {"error": {"code": "MISSING_PARAM", "message": "task_id required"}}
        state_manager = StateManager(paircoder_dir)
        success = state_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        if not success:
            return {"error": {"code": "TASK_NOT_FOUND", "message": f"Task {task_id} not found"}}
        return {"status": "started", "task_id": task_id}

    elif tool_name == "paircoder_task_complete":
        task_id = input_data.get("task_id")
        if not task_id:
            return {"error": {"code": "MISSING_PARAM", "message": "task_id required"}}
        state_manager = StateManager(paircoder_dir)
        success = state_manager.update_task_status(task_id, TaskStatus.DONE)
        if not success:
            return {"error": {"code": "TASK_NOT_FOUND", "message": f"Task {task_id} not found"}}
        return {"status": "completed", "task_id": task_id}

    elif tool_name == "paircoder_context_read":
        file = input_data.get("file", "state")
        file_map = {
            "state": paircoder_dir / "context" / "state.md",
            "project": paircoder_dir / "context" / "project.md",
            "workflow": paircoder_dir / "context" / "workflow.md",
            "config": paircoder_dir / "config.yaml",
            "capabilities": paircoder_dir / "capabilities.yaml",
        }
        if file not in file_map:
            return {"error": {"code": "INVALID_FILE", "message": f"Unknown file: {file}"}}
        file_path = file_map[file]
        if not file_path.exists():
            return {"error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {file_path}"}}
        content = file_path.read_text(encoding="utf-8")
        return {"file": file, "content": content}

    elif tool_name == "paircoder_plan_status":
        plan_id = input_data.get("plan_id")
        state_manager = StateManager(paircoder_dir)
        plan_parser = PlanParser(paircoder_dir / "plans")
        task_parser = TaskParser(paircoder_dir / "tasks")

        if plan_id:
            plan = plan_parser.get_plan_by_id(plan_id)
        else:
            plan_id = state_manager.get_active_plan_id()
            plan = plan_parser.get_plan_by_id(plan_id) if plan_id else None

        if not plan:
            return {"error": {"code": "PLAN_NOT_FOUND", "message": "Plan not found"}}

        tasks = task_parser.get_tasks_for_plan(plan.id)
        task_counts = {"pending": 0, "in_progress": 0, "done": 0, "blocked": 0}
        for task in tasks:
            if task.status.value in task_counts:
                task_counts[task.status.value] += 1

        return {
            "plan": {"id": plan.id, "title": plan.title, "status": plan.status.value},
            "task_counts": task_counts,
        }

    elif tool_name == "paircoder_plan_list":
        plan_parser = PlanParser(paircoder_dir / "plans")
        plans = plan_parser.parse_all()
        return [
            {"id": p.id, "title": p.title, "status": p.status.value}
            for p in plans
        ]

    else:
        return {"error": {"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"}}
