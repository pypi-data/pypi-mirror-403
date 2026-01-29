# PairCoder — AI-Augmented Pair Programming Framework

[![PyPI version](https://badge.fury.io/py/bpsai-pair.svg)](https://badge.fury.io/py/bpsai-pair)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PairCoder is a **repo-native toolkit** for pairing with AI coding agents (Claude, GPT, Codex, Gemini). It standardizes project memory in `.paircoder/`, provides structured workflows via skills, and ships a CLI with **182+ commands** to orchestrate the entire development lifecycle.

## Key Features

| Feature | Description |
|---------|-------------|
| **Planning System** | Plans, sprints, tasks with YAML+MD format |
| **Skills** | Claude Code native skills with cross-platform export |
| **Orchestration** | Multi-agent coordination, model routing by complexity |
| **Autonomous Workflow** | Auto-session for hands-off task execution |
| **Contained Autonomy** | Docker-enforced isolation with three-tier access control |
| **Architecture Enforcement** | File/function size limits with pre-commit/CI gates |
| **Presets** | 8 built-in presets (python-cli, bps, autonomous, etc.) |
| **GitHub Integration** | Auto-PR creation, task-linked PRs, archive on merge |
| **Trello Integration** | Board/card management, progress comments, webhooks |
| **Standup Generation** | Daily summaries in markdown/slack/trello formats |
| **Metrics** | Token tracking, cost estimation, budget enforcement |
| **Time Tracking** | Built-in timer with Toggl integration |
| **MCP Server** | 15 tools for autonomous agent operation |
| **Auto-Hooks** | Automatic Trello sync and state updates on task changes |

## Quick Start

### Install

```bash
pip install bpsai-pair
bpsai-pair --version
```

### Initialize a Project

```bash
# New project with preset
bpsai-pair init my-project --preset python-cli
cd my-project

# List available presets
bpsai-pair preset list

# Initialize with BPS Trello workflow
bpsai-pair init my-project --preset bps

# Existing project
cd your-project
bpsai-pair init .
```

### Optional Dependencies

```bash
# For MCP/Claude Desktop integration
pip install 'bpsai-pair[mcp]'

# For Trello integration
pip install 'bpsai-pair[trello]'

# For Docker sandbox (contained autonomy)
pip install 'bpsai-pair[sandbox]'

# All extras
pip install 'bpsai-pair[mcp,trello,sandbox]'
```

## Project Structure

After initialization, your project will have:

```
my-project/
├── .paircoder/                    # PairCoder data
│   ├── config.yaml               # Project configuration
│   ├── capabilities.yaml         # LLM capability manifest
│   ├── context/                  # Project context files
│   │   ├── project.md           # Project overview
│   │   ├── workflow.md          # Workflow guidelines
│   │   └── state.md             # Current state
│   ├── plans/                    # Plan files (.plan.yaml)
│   ├── tasks/                    # Task files (.task.md)
│   └── history/                  # Archives, metrics
├── .claude/                       # Claude Code native
│   ├── skills/                   # Model-invoked skills
│   ├── agents/                   # Custom subagents
│   └── commands/                 # Slash commands
├── AGENTS.md                      # Universal AI entry point
└── CLAUDE.md                      # Claude Code instructions
```

## CLI Commands (180+)

### Core Commands

| Command | Description |
|---------|-------------|
| `init [path] [--preset]` | Initialize repo with PairCoder structure |
| `feature <name>` | Create feature branch with context |
| `pack [--lite]` | Package context for AI agents |
| `context-sync` | Update the context loop |
| `status` | Show current context and recent changes |
| `validate` | Check repo structure and consistency |

### Planning & Tasks

| Command | Description |
|---------|-------------|
| `plan new <slug>` | Create a new plan |
| `plan list` | List all plans |
| `plan show <id>` | Show plan details |
| `plan status [id]` | Show progress with task breakdown |
| `task list` | List all tasks |
| `task update <id> --status` | Update task status (fires hooks) |

### Trello Integration

| Command | Description |
|---------|-------------|
| `trello connect` | Connect to Trello (store credentials) |
| `trello boards` | List available boards |
| `ttask list` | List tasks from board |
| `ttask start <id>` | Start working on a task |
| `ttask done <id>` | Complete task with summary |

### MCP Server

| Command | Description |
|---------|-------------|
| `mcp serve` | Start MCP server (stdio transport) |
| `mcp tools` | List available tools |
| `mcp test <tool>` | Test a tool locally |

### Contained Autonomy

| Command | Description |
|---------|-------------|
| `contained-auto [task]` | Start contained autonomous session |
| `containment status` | Show containment mode and protected paths |
| `containment rollback` | Rollback to checkpoint |

## Skills System

PairCoder provides Claude Code native skills in `.claude/skills/`:

- **designing-and-implementing** — Feature development workflow
- **implementing-with-tdd** — Test-driven development
- **reviewing-code** — Code review workflow
- **finishing-branches** — Branch completion
- **managing-task-lifecycle** — Task workflow with Trello
- **planning-with-trello** — Planning with Trello integration
- **releasing-versions** — Release preparation workflow

Export skills to other platforms:
```bash
bpsai-pair skill export --format cursor    # Export to Cursor
bpsai-pair skill export --format continue  # Export to Continue.dev
bpsai-pair skill export --format all       # Export to all platforms
```

## Documentation

- [Full Documentation](https://github.com/BPSAI/paircoder#readme) — Complete guide with all 180+ commands
- [User Guide](https://github.com/BPSAI/paircoder/blob/main/.paircoder/docs/USER_GUIDE.md) — Getting started guide
- [Feature Matrix](https://github.com/BPSAI/paircoder/blob/main/.paircoder/docs/FEATURE_MATRIX.md) — Complete feature inventory
- [Contained Autonomy](https://github.com/BPSAI/paircoder/blob/main/docs/CONTAINED_AUTONOMY.md) — Docker isolation guide

## License

PairCoder is proprietary software. See [LICENSE](LICENSE) for terms.

For licensing inquiries, contact info@bpsaisoftware.com
