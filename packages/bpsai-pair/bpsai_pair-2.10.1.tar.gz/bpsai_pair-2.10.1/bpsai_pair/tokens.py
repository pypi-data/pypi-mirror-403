"""Token counting and budget estimation.

Provides accurate token counting using tiktoken for estimating
Claude API context usage and preventing context compaction.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tiktoken


# Model context limits (tokens)
MODEL_LIMITS = {
    "claude-sonnet-4-5": 200000,
    "claude-opus-4-5": 200000,
    "claude-haiku-4-5": 200000,
    # Legacy models
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
}

# Budget thresholds (percentages)
THRESHOLDS = {
    "info": 50,      # 50% - informational
    "warning": 75,   # 75% - consider breaking up
    "critical": 90,  # 90% - compaction likely
}

# Estimation multipliers by task type
TASK_TYPE_MULTIPLIERS = {
    "feature": 1.5,    # New features tend to generate more output
    "bugfix": 1.2,     # Bug fixes moderate output
    "refactor": 1.3,   # Refactors touch many files
    "chore": 1.0,      # Chores are typically small
    "docs": 0.8,       # Docs are lighter on code
}

# Default base context tokens (system prompt, instructions, etc.)
DEFAULT_BASE_CONTEXT = 15000


@dataclass
class TokenEstimate:
    """Token estimate breakdown for a task."""
    base_context: int
    task_file: int
    source_files: int
    estimated_output: int
    total: int
    budget_percent: float


@dataclass
class BudgetStatus:
    """Budget status with thresholds."""
    used: int
    limit: int
    remaining: int
    percent: float
    status: str  # "ok" | "warning" | "critical"
    message: str


def get_encoding(model: str = "cl100k_base") -> tiktoken.Encoding:
    """Get tiktoken encoding for a model.

    Args:
        model: Encoding name or model name. Defaults to cl100k_base
               which is compatible with Claude models.

    Returns:
        tiktoken.Encoding instance
    """
    return tiktoken.get_encoding(model)


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        model: Encoding name. Defaults to cl100k_base (Claude-compatible)

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0
    encoding = get_encoding(model)
    return len(encoding.encode(text))


def count_file_tokens(path: Path) -> int:
    """Count tokens in a file.

    Handles various encodings and binary files gracefully.

    Args:
        path: Path to the file

    Returns:
        Number of tokens, or 0 if file can't be read
    """
    if not path.exists():
        return 0

    # Skip binary files by extension
    binary_extensions = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.bin',
                        '.jpg', '.jpeg', '.png', '.gif', '.ico', '.pdf',
                        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}
    if path.suffix.lower() in binary_extensions:
        return 0

    try:
        # Try UTF-8 first
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # Fall back to latin-1 for legacy files
            content = path.read_text(encoding='latin-1')
        except Exception:
            return 0
    except Exception:
        return 0

    return count_tokens(content)


def estimate_task_tokens(
    task_id: str,
    files: list[Path],
    complexity: int = 10,
    task_type: str = "feature",
    base_context: int = DEFAULT_BASE_CONTEXT
) -> TokenEstimate:
    """Estimate total tokens for a task.

    Args:
        task_id: Task identifier (for finding task file)
        files: List of source files to be read/modified
        complexity: Task complexity score (1-100)
        task_type: Type of task (feature, bugfix, refactor, chore, docs)
        base_context: Base context tokens (system prompt, etc.)

    Returns:
        TokenEstimate with breakdown
    """
    # Count task file tokens (estimate if not found)
    task_file_tokens = 500  # Default estimate
    task_paths = [
        Path(f".paircoder/tasks/{task_id}.task.md"),
        Path(f".paircoder/tasks/TASK-{task_id}.task.md"),
    ]
    for task_path in task_paths:
        if task_path.exists():
            task_file_tokens = count_file_tokens(task_path)
            break

    # Count source file tokens
    source_tokens = sum(count_file_tokens(f) for f in files)

    # Estimate output tokens based on complexity and task type
    multiplier = TASK_TYPE_MULTIPLIERS.get(task_type, 1.0)
    # Scale output estimate: base 1000 tokens + complexity factor
    estimated_output = int((1000 + complexity * 50) * multiplier)

    # Calculate total
    total = base_context + task_file_tokens + source_tokens + estimated_output

    # Calculate budget percentage (assume 200k limit)
    budget_percent = round((total / 200000) * 100, 1)

    return TokenEstimate(
        base_context=base_context,
        task_file=task_file_tokens,
        source_files=source_tokens,
        estimated_output=estimated_output,
        total=total,
        budget_percent=budget_percent
    )


def get_budget_status(
    estimated: int,
    model: str = "claude-sonnet-4-5"
) -> BudgetStatus:
    """Get budget status with thresholds.

    Args:
        estimated: Estimated token usage
        model: Model name to get limit for

    Returns:
        BudgetStatus with usage info and status level
    """
    limit = MODEL_LIMITS.get(model, 200000)
    remaining = max(0, limit - estimated)
    percent = round((estimated / limit) * 100, 1)

    # Determine status
    if percent >= THRESHOLDS["critical"]:
        status = "critical"
        message = "Context compaction likely! Consider breaking up the task."
    elif percent >= THRESHOLDS["warning"]:
        status = "warning"
        message = "Approaching context limit. Monitor closely."
    elif percent >= THRESHOLDS["info"]:
        status = "info"
        message = "Budget at 50%. Plan remaining work carefully."
    else:
        status = "ok"
        message = "Budget healthy."

    return BudgetStatus(
        used=estimated,
        limit=limit,
        remaining=remaining,
        percent=percent,
        status=status,
        message=message
    )


def estimate_from_task_file(task_path: Path) -> Optional[TokenEstimate]:
    """Estimate tokens from a task file by parsing its contents.

    Extracts:
    - Complexity from frontmatter
    - Task type from frontmatter
    - Files to modify from "Files to Modify" section

    Args:
        task_path: Path to the .task.md file

    Returns:
        TokenEstimate or None if file can't be parsed
    """
    if not task_path.exists():
        return None

    try:
        content = task_path.read_text(encoding='utf-8')
    except Exception:
        return None

    # Parse frontmatter
    complexity = 10
    task_type = "feature"
    task_id = task_path.stem.replace('.task', '')

    if content.startswith('---'):
        try:
            end_idx = content.index('---', 3)
            frontmatter = content[3:end_idx]
            for line in frontmatter.split('\n'):
                if line.startswith('complexity:'):
                    try:
                        complexity = int(line.split(':')[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('type:'):
                    task_type = line.split(':')[1].strip()
                elif line.startswith('id:'):
                    task_id = line.split(':')[1].strip()
        except ValueError:
            pass

    # Parse "Files to Modify" section
    files = []
    in_files_section = False
    for line in content.split('\n'):
        if '## Files to Modify' in line or '## Files to Create' in line:
            in_files_section = True
            continue
        if in_files_section:
            if line.startswith('##'):
                break
            if line.strip().startswith('- '):
                # Extract file path from markdown list
                file_str = line.strip()[2:].split()[0].strip('`')
                file_path = Path(file_str)
                if file_path.exists():
                    files.append(file_path)

    return estimate_task_tokens(
        task_id=task_id,
        files=files,
        complexity=complexity,
        task_type=task_type
    )
