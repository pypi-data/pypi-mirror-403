"""
Orchestration module for multi-agent coordination.

This module provides:
- HeadlessSession: Programmatic Claude Code invocation
- HandoffManager: Context packaging for agent transfers
- Orchestrator: Task routing and agent coordination
- AgentInvoker: Invoke specialized agents from .claude/agents/
- PlannerAgent: Design and planning specialist agent
- ReviewerAgent: Code review specialist agent
- SecurityAgent: Pre-execution security gatekeeper agent
"""

from .headless import HeadlessSession, HeadlessResponse
from .handoff import (
    HandoffManager,
    HandoffPackage,
    EnhancedHandoffPackage,
    HandoffChain,
    HandoffSerializer,
    prepare_handoff,
    receive_handoff,
)
from .orchestrator import Orchestrator
from .invoker import AgentDefinition, AgentInvoker, InvocationResult, invoke_agent
from .planner import PlannerAgent, PlanOutput, PlanPhase, invoke_planner, should_trigger_planner
from .reviewer import (
    ReviewerAgent,
    ReviewOutput,
    ReviewItem,
    ReviewSeverity,
    ReviewVerdict,
    invoke_reviewer,
    should_trigger_reviewer,
    extract_changed_files,
    extract_line_changes,
)
from .security import (
    SecurityAgent,
    SecurityDecision,
    SecurityFinding,
    SecurityAction,
    invoke_security,
    should_trigger_security,
)
from .agent_selector import (
    AgentSelector,
    AgentMatch,
    SelectionCriteria,
    select_agent_for_task,
)

__all__ = [
    "HeadlessSession",
    "HeadlessResponse",
    "HandoffManager",
    "HandoffPackage",
    "EnhancedHandoffPackage",
    "HandoffChain",
    "HandoffSerializer",
    "prepare_handoff",
    "receive_handoff",
    "Orchestrator",
    "AgentDefinition",
    "AgentInvoker",
    "InvocationResult",
    "invoke_agent",
    "PlannerAgent",
    "PlanOutput",
    "PlanPhase",
    "invoke_planner",
    "should_trigger_planner",
    "ReviewerAgent",
    "ReviewOutput",
    "ReviewItem",
    "ReviewSeverity",
    "ReviewVerdict",
    "invoke_reviewer",
    "should_trigger_reviewer",
    "extract_changed_files",
    "extract_line_changes",
    "SecurityAgent",
    "SecurityDecision",
    "SecurityFinding",
    "SecurityAction",
    "invoke_security",
    "should_trigger_security",
    "AgentSelector",
    "AgentMatch",
    "SelectionCriteria",
    "select_agent_for_task",
]
