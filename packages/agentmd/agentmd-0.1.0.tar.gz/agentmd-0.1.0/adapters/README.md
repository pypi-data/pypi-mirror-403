# AGENT.md Adapters

Adapters convert AGENT.md (YAML frontmatter + Markdown body) into tool-specific instruction files.

## Supported targets

| Target   | Output path                         | Format |
|----------|-------------------------------------|--------|
| Cursor   | `.cursor/rules/agent-from-agentmd.mdc` | Markdown with frontmatter (`description`, `globs`, `alwaysApply`) |
| Claude   | `claude.md`                         | Markdown sections (Role, Priorities, Context, Tech, Rules, Change policy, Output) |
| Copilot  | `.github/agents/agent.agent.md`     | YAML frontmatter (`name`, `description`) + Markdown body |

## Field mapping

### AGENT.md → Cursor (`.mdc`)

| AGENT.md              | Cursor frontmatter / body     |
|-----------------------|-------------------------------|
| `description`         | `description`                 |
| `globs`               | `globs` (array)               |
| `alwaysApply`         | `alwaysApply`                 |
| `role`, `priorities`, `context`, `tech`, `rules`, `change-policy`, `output` | Rendered as `## Role`, `## Priorities`, etc. in the rule body |
| body                  | Appended after structured sections |

### AGENT.md → Claude (`claude.md`)

| AGENT.md              | claude.md                     |
|-----------------------|-------------------------------|
| `name`                | `# {name}`                    |
| `description`         | Top-level paragraph           |
| `role`                | `## Role`                     |
| `priorities`          | `## Priorities` (bullets)     |
| `context`             | `## Context`                  |
| `tech`                | `## Tech`                     |
| `rules`               | `## Rules`                    |
| `change-policy`       | `## Change policy`            |
| `output`              | `## Output`                  |
| body                  | Appended                     |

### AGENT.md → Copilot (`.agent.md`)

| AGENT.md              | Copilot frontmatter / body    |
|-----------------------|-------------------------------|
| `name`                | `name`                        |
| `description` or `role` | `description` (required)    |
| `role`, `priorities`, `tech`, `rules`, `change-policy` | Rendered in the Markdown body |
| body                  | Appended                     |

## Cursor template (`.mdc`)

Cursor expects a rule file with optional frontmatter:

```yaml
---
description: "Short description for when to apply this rule"
globs: ["*.ts", "src/**"]
alwaysApply: false
---

## Role
Senior backend engineer

## Priorities
- correctness
- security

## Rules
- Use TypeScript strict mode
- Validate request body with Zod
```

The `agentmd generate --target cursor` output follows this pattern, with `description`/`globs`/`alwaysApply` taken from AGENT.md and the rest from `role`, `priorities`, `tech`, `rules`, `change-policy`, `output`, and the body.

## Claude template (`claude.md`)

Claude reads a single `claude.md` with clear sections:

```markdown
# Project name

One-sentence description.

## Role
Senior backend engineer

## Priorities
- correctness
- security

## Rules
- Use TypeScript strict mode
```

`agentmd generate --target claude` produces this from AGENT.md.

## Copilot template (`.agent.md`)

GitHub Copilot custom agents use YAML frontmatter plus a body:

```yaml
---
name: my-agent
description: "Focuses on backend API development and testing"
---

**Role:** Senior backend engineer

**Rules:**
- Use TypeScript strict mode
```

`agentmd generate --target copilot` produces this. The `description` field is required by Copilot; we use `description` or `role` from AGENT.md.

## Extending

To add a new adapter:

1. Implement a function `adapter_<name>(fm: dict, body: str) -> str`.
2. Add a `write_<name>(fm, body, out_dir: Path) -> Path` that writes the output to the correct path.
3. Register the target in the CLI `_cmd_generate` and in `adapters.py`.

The same AGENT.md can be used for all targets; only the output format and location differ.
