"""Context file templates for PairCoder.

This module contains templates for generating context files during
project initialization.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config_loader import Config


class ContextTemplate:
    """Templates for context files."""

    @staticmethod
    def development_md(config: "Config") -> str:
        """Generate development.md template."""
        return f"""# Development Log

**Project:** {config.project_name}
**Phase:** Phase 1: Initial Setup
**Primary Goal:** {config.primary_goal}

## KPIs & Non-Functional Targets

- Test Coverage: ≥ {config.coverage_target}%
- Documentation: Complete for all public APIs
- Performance: Response time < 200ms (p95)

## Phase 1 — Foundation (Weeks 1–2)

**Objectives**
- Set up project structure and CI/CD
- Define core architecture and interfaces
- Establish testing framework

**Tasks**
- [ ] Initialize repository with PairCoder
- [ ] Set up CI workflows
- [ ] Create initial project structure
- [ ] Write architectural decision records

**Testing Plan**
- Unit tests for all business logic
- Integration tests for external boundaries
- End-to-end tests for critical user flows

**Risks & Rollback**
- Risk: Incomplete requirements — Mitigation: Regular stakeholder reviews
- Rollback: Git revert with documented rollback procedures

## Context Sync (AUTO-UPDATED)

- **Overall goal is:** {config.primary_goal}
- **Last action was:** Initialized project
- **Next action will be:** Set up CI/CD pipeline
- **Blockers:** None
"""

    @staticmethod
    def agents_md(config: "Config") -> str:
        """Generate agents.md template."""
        return f"""# Agents Guide — AI Pair Coding Playbook

**Project:** {config.project_name}
**Purpose:** {config.primary_goal}

## Ground Rules

1. **Context is King**: Always refer to `.paircoder/context/state.md` for current state
2. **Test First**: Write tests before implementation
3. **Small Changes**: Keep PRs under 200 lines when possible
4. **Update Loop**: Run `bpsai-pair context-sync` after every significant change

## Project Structure (v2.1)

```
.
├── .paircoder/                    # All PairCoder configuration
│   ├── config.yaml               # Configuration
│   ├── context/                  # Project context (moved from root)
│   │   ├── state.md              # Current state
│   │   ├── project.md            # Project overview
│   │   └── workflow.md           # Development workflow
│   ├── flows/                    # Workflow definitions
│   ├── plans/                    # Plan files
│   └── tasks/                    # Task files
├── .claude/                       # Claude Code native (if used)
├── AGENTS.md                      # Universal entry point
├── CLAUDE.md                      # Claude Code pointer
├── src/                           # Source code
├── tests/                         # Test suites
└── docs/                          # Documentation
```

## Workflow

1. Check status: `bpsai-pair status`
2. Create feature: `bpsai-pair feature <name> --primary "<goal>" --phase "<phase>"`
3. Make changes (with tests)
4. Update context: `bpsai-pair context-sync --last "<what>" --next "<next>"`
5. Create pack: `bpsai-pair pack`
6. Share with AI agent

## Testing Requirements

- Minimum coverage: {config.coverage_target}%
- All new code must have tests
- Integration tests for external dependencies
- Performance tests for critical paths

## Code Style

- Python: {config.python_formatter} for formatting and linting
- JavaScript: {config.node_formatter} for formatting
- Commit messages: Conventional Commits format
- Branch names: {config.default_branch_type}/<description>

## Context Loop Protocol

After EVERY meaningful change:
```bash
bpsai-pair context-sync \\
    --last "What was just completed" \\
    --next "The immediate next step" \\
    --blockers "Any impediments"
```

## Excluded from Context

The following are excluded from agent packs (see `.agentpackignore`):
{chr(10).join(f'- {exclude}' for exclude in config.pack_excludes)}

## Commands Reference

- `bpsai-pair init` - Initialize scaffolding
- `bpsai-pair feature` - Create feature branch
- `bpsai-pair pack` - Create context package
- `bpsai-pair sync` - Update context loop
- `bpsai-pair status` - Show current state
- `bpsai-pair validate` - Check structure
- `bpsai-pair ci` - Run local CI checks
"""

    @staticmethod
    def gitignore() -> str:
        """Generate .gitignore template."""
        return """# PairCoder
.paircoder.yml.local
.paircoder/config.local.yaml
.paircoder/config.local.yml
agent_pack*.tgz
*.bak

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# OS
Thumbs.db
Desktop.ini
"""
