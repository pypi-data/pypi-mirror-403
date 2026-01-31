# bpsai-pair

> AI-augmented pair programming framework with 182+ CLI commands

[![PyPI version](https://badge.fury.io/py/bpsai-pair.svg)](https://pypi.org/project/bpsai-pair/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

## Overview

**bpsai-pair** (PairCoder) is a comprehensive AI pair programming framework that provides:

- **Planning & Task Management** — Create and manage development plans, tasks, and sprints
- **Skill-Based Workflows** — Pre-built workflows for TDD, code review, releases, and more
- **Integration Hub** — Connect with Trello, GitHub, MCP servers, and time tracking
- **Token Budget Management** — Track and control AI token usage across sessions
- **Enforcement Gates** — Architecture checks, acceptance criteria validation, and state machines
- **Interactive Setup Wizard** — GUI-based project configuration with tier-aware features

## Installation

```bash
# Core installation
pip install bpsai-pair

# With optional integrations
pip install bpsai-pair[trello]      # Trello integration
pip install bpsai-pair[wizard]      # Interactive setup wizard
pip install bpsai-pair[all]         # All extras
```

## Quick Start

```bash
# Initialize a new project
bpsai-pair init

# Or use the interactive wizard (requires wizard extras)
bpsai-pair wizard

# Check project status
bpsai-pair status

# Create a feature plan
bpsai-pair feature my-feature --type feature --primary "Build amazing things"

# List available skills
bpsai-pair skill list

# Pack context for AI assistants
bpsai-pair pack
```

## License Tiers

- **Solo** — Core planning, skills, enforcement, guided setup
- **Pro** — Trello, GitHub, MCP, token budget, cost tracking, model routing
- **Team** — Multi-user collaboration features
- **Enterprise** — Remote access, SSO, multi-workspace, advanced security

Check your license: `bpsai-pair license status`

## Documentation

- [GitHub Repository](https://github.com/BPSAI/paircoder)
- [Changelog](https://github.com/BPSAI/paircoder/blob/main/CHANGELOG.md)
- [Issue Tracker](https://github.com/BPSAI/paircoder/issues)

## Requirements

- Python 3.10 or higher
- Git (for project management features)

## Support

- Report issues: [GitHub Issues](https://github.com/BPSAI/paircoder/issues)
- Email: dev@bpsai.com
