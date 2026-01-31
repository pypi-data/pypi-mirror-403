# Project Context

## What Is This Project?

**Project:** {{ cookiecutter.project_name }}
**Primary Goal:** {{ cookiecutter.primary_goal }}
**Test Coverage Target:** {{ cookiecutter.coverage_target }}

<!-- Describe your project's purpose and value in 2-3 sentences -->

## Repository Structure

```
{{ cookiecutter.project_slug }}/
├── .paircoder/              # PairCoder system files
│   ├── config.yaml          # Project configuration
│   ├── capabilities.yaml    # LLM capability manifest
│   ├── context/             # Project memory (project.md, state.md, workflow.md)
│   ├── plans/               # Active plans
│   └── tasks/               # Task files by plan
├── .claude/                 # Claude Code configuration
│   ├── agents/              # Custom agent definitions
│   ├── skills/              # Model-invoked skills
│   └── settings.json        # Hooks configuration
├── src/                     # Source code
├── tests/                   # Test files
└── docs/                    # Documentation
```

## Tech Stack

<!-- Update with your actual tech stack -->
- **Language:** TBD
- **Framework:** TBD
- **Database:** TBD
- **Testing:** TBD

## Key Constraints

| Constraint | Requirement |
|------------|-------------|
| **Test Coverage** | Minimum {{ cookiecutter.coverage_target }} coverage |
| **Dependencies** | Review required for new deps |
| **Secrets** | Never commit secrets or credentials |
| **Compatibility** | No breaking changes without major version |

## Architecture Principles

<!-- Update these to match your project's principles -->

1. **Principle 1** — Description
2. **Principle 2** — Description
3. **Principle 3** — Description

## How to Work Here

1. Read `.paircoder/context/state.md` for current plan/task status
2. Check `.paircoder/capabilities.yaml` to understand available actions
3. Follow the active skill for structured work
4. Update `state.md` after completing significant work

## Key Files

| File | Purpose |
|------|---------|
| `.paircoder/config.yaml` | Project configuration |
| `.paircoder/capabilities.yaml` | What LLMs can do here |
| `.paircoder/context/state.md` | Current status and active work |
| `src/` | Source code |
| `tests/` | Test files |

## Team

| Role | Handle |
|------|--------|
| Owner | @{{ cookiecutter.owner_gh_handle }} |
| Architect | @{{ cookiecutter.architect_gh_handle }} |
| Build | @{{ cookiecutter.build_gh_handle }} |
| QA | @{{ cookiecutter.qa_gh_handle }} |
| SRE | @{{ cookiecutter.sre_gh_handle }} |

## External Resources

<!-- Add links to relevant documentation, APIs, etc. -->
- Documentation: TBD
- Issue Tracker: TBD
- CI/CD: TBD

## Testing

```bash
# Run tests (update with your actual command)
pytest

# Or for Node projects
npm test
```

## Building

```bash
# Build (update with your actual command)
pip install -e .

# Or for Node projects
npm run build
```
