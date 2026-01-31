---
description: Enter Release Engineer role to prepare a release with validation
allowed-tools: Bash(bpsai-pair:*), Bash(git:*), Bash(pytest:*), Bash(pip:*), Bash(grep:*), Bash(diff:*), Bash(rm:*), Bash(cd:*), Bash(ls:*)
argument-hint: <version>
---

Enter **Release Engineer role** to prepare release. Dispatch `reviewer` and `security-auditor` agents as necessary.

**Version**: $ARGUMENTS (e.g., `v2.9.0` or `2.9.0`)

## Pre-Flight (Enforcement)

```bash
bpsai-pair task list --status in_progress
bpsai-pair task list --status blocked
pytest tests/ -v --tb=short
bpsai-pair security scan-secrets
```

**BLOCKERS**: Incomplete tasks, failing tests, or secrets = cannot release.

## Execute Workflow

Read and follow `.claude/skills/releasing-versions/SKILL.md` for the complete workflow.

## Key Constraints

- Version format: `X.Y.Z` in files, `vX.Y.Z` for git tags
- Security scans are BLOCKERS, not warnings
- User must explicitly approve the push
- All tests must pass with ≥80% coverage
- CHANGELOG follows Keep a Changelog format

## Files to Update

| File | Field |
|------|-------|
| `tools/cli/pyproject.toml` | `version = "X.Y.Z"` |
| `tools/cli/bpsai_pair/__init__.py` | `__version__ = "X.Y.Z"` |
| `.paircoder/capabilities.yaml` | `version: "X.Y.Z"` |
| `.paircoder/config.yaml` | `version: "X.Y.Z"` |
| `CHANGELOG.md` | New version entry |
