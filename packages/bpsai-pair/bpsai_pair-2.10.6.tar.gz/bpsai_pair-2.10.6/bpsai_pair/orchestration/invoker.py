"""
Agent Invocation Framework.

Provides programmatic invocation of specialized agents defined in .claude/agents/*.md.
Each agent has a specific role (planner, reviewer, security) with its own system prompt
and permission mode.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .headless import HeadlessSession, PermissionMode

logger = logging.getLogger(__name__)

# Default location for agent definitions
DEFAULT_AGENTS_DIR = ".claude/agents"

# Model mapping from agent definitions to Claude model flags
MODEL_MAP = {
    "sonnet": "sonnet",
    "opus": "opus",
    "haiku": "haiku",
}


@dataclass
class AgentDefinition:
    """
    Agent definition loaded from .claude/agents/<name>.md.

    The agent file format is:
    ```
    ---
    name: agent-name
    description: Short description of the agent
    tools: Read, Grep, Glob, Bash
    model: sonnet
    permissionMode: plan
    skills: optional-skill-name
    ---

    # Agent Title

    System prompt content...
    ```
    """

    name: str
    description: str
    model: str  # sonnet, opus, haiku
    permission_mode: PermissionMode  # plan, auto, full
    tools: list[str]
    system_prompt: str  # Body content after YAML frontmatter
    skills: Optional[str] = None  # Optional linked skill
    source_file: Optional[Path] = None  # Path to source .md file

    @classmethod
    def from_file(cls, path: Path) -> "AgentDefinition":
        """
        Load an agent definition from a markdown file.

        Args:
            path: Path to the .md file

        Returns:
            AgentDefinition parsed from the file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError(f"Invalid agent file format (no YAML frontmatter): {path}")

        frontmatter_yaml = frontmatter_match.group(1)
        body = frontmatter_match.group(2).strip()

        try:
            metadata = yaml.safe_load(frontmatter_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {path}: {e}")

        if not metadata:
            raise ValueError(f"Empty frontmatter in {path}")

        # Validate required fields
        required_fields = ["name", "description", "model", "permissionMode"]
        missing = [f for f in required_fields if f not in metadata]
        if missing:
            raise ValueError(f"Missing required fields in {path}: {missing}")

        # Parse tools list
        tools_raw = metadata.get("tools", "")
        if isinstance(tools_raw, str):
            tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
        elif isinstance(tools_raw, list):
            tools = tools_raw
        else:
            tools = []

        return cls(
            name=metadata["name"],
            description=metadata["description"],
            model=metadata["model"],
            permission_mode=metadata["permissionMode"],
            tools=tools,
            system_prompt=body,
            skills=metadata.get("skills"),
            source_file=path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "permission_mode": self.permission_mode,
            "tools": self.tools,
            "skills": self.skills,
            "source_file": str(self.source_file) if self.source_file else None,
        }


@dataclass
class InvocationResult:
    """
    Result from invoking an agent.

    Contains both the response content and metadata about the invocation.
    """

    success: bool
    output: str
    agent_name: str
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    session_id: Optional[str] = None
    error: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        """Total tokens used in this invocation."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "output": self.output,
            "agent_name": self.agent_name,
            "cost_usd": self.cost_usd,
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            },
            "duration_seconds": self.duration_seconds,
            "session_id": self.session_id,
            "error": self.error,
        }


@dataclass
class AgentInvoker:
    """
    Invokes specialized agents defined in .claude/agents/*.md.

    The invoker:
    1. Loads agent definitions from markdown files
    2. Builds prompts with the agent's system prompt + user context
    3. Invokes via HeadlessSession with the correct permission mode
    4. Returns structured results

    Example:
        >>> invoker = AgentInvoker()
        >>> result = invoker.invoke("planner", "Design an authentication system")
        >>> print(result.output)
    """

    agents_dir: Path = field(default_factory=lambda: Path(DEFAULT_AGENTS_DIR))
    working_dir: Optional[Path] = None
    timeout_seconds: int = 300
    _agents_cache: dict[str, AgentDefinition] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Resolve agents directory relative to working directory."""
        if not self.agents_dir.is_absolute():
            base = self.working_dir or Path.cwd()
            self.agents_dir = base / self.agents_dir

    def load_agent(self, name: str) -> AgentDefinition:
        """
        Load an agent definition by name.

        Args:
            name: Agent name (e.g., 'planner', 'reviewer', 'security')

        Returns:
            AgentDefinition for the named agent

        Raises:
            FileNotFoundError: If agent file doesn't exist
            ValueError: If agent file is invalid
        """
        # Check cache first
        if name in self._agents_cache:
            return self._agents_cache[name]

        # Find agent file
        agent_file = self.agents_dir / f"{name}.md"
        if not agent_file.exists():
            raise FileNotFoundError(
                f"Agent '{name}' not found. Expected file: {agent_file}"
            )

        agent = AgentDefinition.from_file(agent_file)
        self._agents_cache[name] = agent

        logger.info(f"Loaded agent: {name} (model={agent.model}, mode={agent.permission_mode})")
        return agent

    def list_agents(self) -> list[AgentDefinition]:
        """
        List all available agents.

        Returns:
            List of AgentDefinition for all agents in agents_dir
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return []

        agents = []
        for agent_file in self.agents_dir.glob("*.md"):
            try:
                agent = AgentDefinition.from_file(agent_file)
                agents.append(agent)
            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Failed to load agent {agent_file}: {e}")

        return agents

    def invoke(
        self,
        agent: AgentDefinition | str,
        context: str,
        *,
        system_prompt_prefix: Optional[str] = None,
        system_prompt_suffix: Optional[str] = None,
    ) -> InvocationResult:
        """
        Invoke an agent with the given context.

        The prompt sent to Claude Code is:
        [system_prompt_prefix]
        [agent.system_prompt]
        [system_prompt_suffix]

        ---

        [context]

        Args:
            agent: AgentDefinition or agent name to invoke
            context: The task context/prompt to send to the agent
            system_prompt_prefix: Optional content to prepend to system prompt
            system_prompt_suffix: Optional content to append to system prompt

        Returns:
            InvocationResult with output and metadata
        """
        # Load agent if name provided
        if isinstance(agent, str):
            agent = self.load_agent(agent)

        # Build full prompt
        prompt_parts = []

        if system_prompt_prefix:
            prompt_parts.append(system_prompt_prefix)

        prompt_parts.append(agent.system_prompt)

        if system_prompt_suffix:
            prompt_parts.append(system_prompt_suffix)

        prompt_parts.append("---")
        prompt_parts.append(context)

        full_prompt = "\n\n".join(prompt_parts)

        # Create session with agent's permission mode
        session = HeadlessSession(
            permission_mode=agent.permission_mode,
            working_dir=self.working_dir,
            timeout_seconds=self.timeout_seconds,
        )

        logger.info(
            f"Invoking agent '{agent.name}' "
            f"(model={agent.model}, mode={agent.permission_mode})"
        )

        # Invoke
        response = session.invoke(full_prompt)

        # Convert to InvocationResult
        if response.is_error:
            return InvocationResult(
                success=False,
                output="",
                agent_name=agent.name,
                error=response.error_message,
                duration_seconds=response.duration_seconds,
            )

        return InvocationResult(
            success=True,
            output=response.result,
            agent_name=agent.name,
            cost_usd=response.cost_usd,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            duration_seconds=response.duration_seconds,
            session_id=response.session_id,
        )

    def invoke_with_handoff(
        self,
        agent: AgentDefinition | str,
        context: str,
        handoff_from: Optional[str] = None,
        handoff_context: Optional[str] = None,
    ) -> InvocationResult:
        """
        Invoke an agent with handoff context from another agent.

        This is used when one agent hands off work to another,
        providing previous context and instructions.

        Args:
            agent: Agent to invoke
            context: Current task context
            handoff_from: Name of the agent handing off
            handoff_context: Previous work/context from handoff agent

        Returns:
            InvocationResult with output and metadata
        """
        handoff_prefix = None
        if handoff_from and handoff_context:
            handoff_prefix = f"""## Handoff from {handoff_from}

The {handoff_from} agent has provided the following context for you:

{handoff_context}

---

Now proceed with your role."""

        return self.invoke(
            agent,
            context,
            system_prompt_prefix=handoff_prefix,
        )


# Convenience function for one-shot invocation
def invoke_agent(
    agent_name: str,
    context: str,
    *,
    agents_dir: Optional[Path] = None,
    working_dir: Optional[Path] = None,
    timeout: int = 300,
) -> InvocationResult:
    """
    One-shot agent invocation.

    Convenience function for simple, single-prompt agent invocations.

    Args:
        agent_name: Name of the agent to invoke
        context: The task context/prompt
        agents_dir: Directory containing agent definitions
        working_dir: Working directory for the command
        timeout: Timeout in seconds

    Returns:
        InvocationResult with output and metadata

    Example:
        >>> result = invoke_agent("planner", "Design an authentication system")
        >>> print(result.output)
    """
    invoker = AgentInvoker(
        agents_dir=agents_dir or Path(DEFAULT_AGENTS_DIR),
        working_dir=working_dir,
        timeout_seconds=timeout,
    )
    return invoker.invoke(agent_name, context)
