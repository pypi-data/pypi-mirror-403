# PairCoder Cookiecutter Template

This template provides scaffolding for new PairCoder projects.

## Config Generation

**Note:** `config.yaml` is intentionally NOT included in this template.

Configuration is generated dynamically by one of these methods:

1. **`bpsai-pair init --preset <name>`** - Uses preset.to_config_dict() to generate
   a complete config with all sections (models, routing, hooks, trello, etc.)

2. **`bpsai-pair wizard`** - Interactive web-based guided configuration that
   generates config based on user choices

3. **`Config.save()`** - Programmatic generation (used internally)

This approach ensures that:
- Configs always match the current schema version
- All required sections are present
- No stale template variables in config files
- Consistent structure between init and wizard

## What IS Included

- `.paircoder/` - PairCoder configuration directory
  - `context/` - Context files (state.md, project.md, workflow.md)
  - `plans/` - Plan storage
  - `tasks/` - Task storage
  - `security/` - Security allowlists
  - `capabilities.yaml` - Agent capabilities

- `.claude/` - Claude Code integration
  - `agents/` - Custom agent definitions
  - `skills/` - Skill definitions
  - `settings.json` - Claude Code settings

## Usage

This template is used internally by `bpsai-pair init`. You typically don't
need to use cookiecutter directly. Instead:

```bash
# Initialize a new project
bpsai-pair init --preset python-cli

# Or use the interactive wizard
bpsai-pair wizard
```
