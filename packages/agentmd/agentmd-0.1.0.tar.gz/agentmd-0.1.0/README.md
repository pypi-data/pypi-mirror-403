# AGENT.md

**An open, tool-agnostic standard for defining AI agent project guidelines.**

[Spec](spec/SPEC.md) · [Schema](schema/agentmd.schema.json) · [Examples](examples/)

AGENT.md gives you a **single, schema-validated definition** of how AI coding agents should work in your project. From one `AGENT.md` file, you can generate tool-specific instruction files for **Cursor**, **Claude**, **GitHub Copilot**, and others—keeping your rules in one place while staying compatible with each tool.

---

## What is AGENT.md?

AGENT.md is a project file that describes:

- **Who** the agent is (role, context)
- **What** matters most (priorities, tech stack, rules)
- **How** to change code (branching, commits, reviews)
- **What** to produce (docs, formats, conventions)

It uses:

1. **YAML frontmatter** — Structured, schema-validated metadata (`version`, `role`, `context`, `priorities`, `tech`, `rules`, `change-policy`, `output`, etc.)
2. **Markdown body** — Human-friendly sections for setup, testing, code style, and more

Think of it as a **README for AI agents** that is both machine-parseable and human-editable.

---

## Why AGENT.md?

| Need | AGENT.md |
|------|----------|
| **One source of truth** | Write once; generate Cursor rules, `claude.md`, Copilot agents |
| **Validation** | `agentmd lint` checks frontmatter against the schema before you commit |
| **Consistency** | Same priorities, rules, and change-policy across all generated outputs |
| **Evolve safely** | `version` and schema let format and tooling evolve without breaking existing files |

### How it differs from tool-specific guidance

| File | Scope | Schema | Generation |
|------|-------|--------|------------|
| **AGENT.md** | Tool-agnostic, one definition | Yes (JSON Schema) | Feeds adapters → Cursor, Claude, Copilot |
| **AGENTS.md** | Free-form Markdown; no frontmatter | No | Consumed directly by many agents |
| **.cursor/rules/*.mdc** | Cursor only | Cursor’s frontmatter | Produced by AGENT.md → Cursor adapter |
| **claude.md** | Claude only | No | Produced by AGENT.md → Claude adapter |
| **.github/agents/*.agent.md** | GitHub Copilot only | Copilot’s frontmatter | Produced by AGENT.md → Copilot adapter |

- **AGENTS.md** is intentionally minimal: plain Markdown, no schema. Great when you want a quick, universal set of hints.
- **AGENT.md** adds structure: frontmatter + optional body. Use it when you want to **validate**, **extend** (`extends`), and **generate** tool-specific files from one place.

You can use **both** in a project: e.g. a short `AGENTS.md` for generic “read this first” and a richer `AGENT.md` for teams that use the CLI and adapters.

---

## Quick start

### 1. Create AGENT.md

Put `AGENT.md` at your project root. Minimal example:

```yaml
---
version: "1.0"
---

## Setup
- `pnpm install`
- `pnpm dev`

## Testing
- `pnpm test`
```

### 2. Optional: use the CLI

```bash
# Scaffold a new AGENT.md
agentmd init

# Validate frontmatter against the schema
agentmd lint

# Generate Cursor, Claude, and Copilot files from AGENT.md
agentmd generate
```

### 3. (Optional) Generate tool-specific files

`agentmd generate` writes:

- **Cursor:** `.cursor/rules/agent-from-agentmd.mdc`
- **Claude:** `claude.md`
- **Copilot:** `.github/agents/agent.agent.md`

You can choose targets, e.g. `agentmd generate --target cursor,claude`.

---

## How to write AGENT.md

### Frontmatter (optional but recommended)

When you use frontmatter, **`version` is required**. Everything else is optional.

| Field | Purpose |
|-------|---------|
| `version` | Schema version, e.g. `"1.0"` (required) |
| `name` | Short name for the profile (e.g. for Copilot) |
| `description` | One-sentence purpose of the agent |
| `role` | Persona, e.g. `"Senior backend engineer"` |
| `context` | `project`, `domain`, `audience` (or a string) |
| `priorities` | Ordered list, e.g. `["correctness", "security"]` |
| `tech` | `stack`, `versions`, `constraints` |
| `rules` | List of strings or `{ description, globs?, id? }` |
| `change-policy` | `branching`, `commits`, `reviews`, `breaking` |
| `output` | `formats`, `conventions`, `docs` |
| `extends` | Path or URL to a parent AGENT.md |
| `globs` | File patterns for path-scoped rules |
| `alwaysApply` | Hint for “always apply” where supported |

Full spec: [spec/SPEC.md](spec/SPEC.md). Schema: [schema/agentmd.schema.json](schema/agentmd.schema.json).

### Markdown body

Use normal Markdown. These sections are **conventional** and work well with adapters:

- `## Setup` — Install, env, run
- `## Testing` — How to run tests and CI
- `## Code Style` — Lint, format, naming
- `## Architecture` — Patterns and layers
- `## Security` — Sensitive data, safeguards
- `## Deployment` — Build and release

### Extending another AGENT.md

```yaml
---
version: "1.0"
extends: "../AGENT.md"   # or a URL
priorities: [performance]  # overrides parent’s priorities for this key
---
```

The parent’s frontmatter is deep-merged; the child overrides. The child’s body replaces the parent’s body.

---

## How to extend AGENT.md

1. **New frontmatter fields**  
   Add them in your AGENT.md. The schema allows `additionalProperties: true`, so extra keys are kept. For shared tooling, you can propose new optional fields in the [schema](schema/agentmd.schema.json) and [spec](spec/SPEC.md).

2. **Custom body sections**  
   Add any `## Section` you need. Adapters can pass them through or map them to tool-specific sections.

3. **New adapters**  
   Implement a writer that (a) parses AGENT.md (frontmatter + body), (b) optionally resolves `extends`, and (c) emits the target format. See [adapters/](adapters/) for the built-in Cursor, Claude, and Copilot templates.

4. **Schema evolution**  
   The `version` in frontmatter tracks the schema. New optional properties are minor additions; breaking changes to existing required/optional structure should bump the spec’s major version.

---

## CLI: `agentmd`

| Command | Description |
|---------|-------------|
| `agentmd init` | Create a scaffold `AGENT.md` in the current directory |
| `agentmd lint` | Parse AGENT.md and validate frontmatter against the schema |
| `agentmd generate` | Produce tool-specific files (Cursor, Claude, Copilot) from AGENT.md |

### Install

```bash
pip install -e .   # from the repo root
# or
pip install agentmd   # when published
```

### Examples

```bash
agentmd init
agentmd lint
agentmd generate
agentmd generate --target cursor,claude --out .cursor/rules,.
```

---

## Adapters

Adapters turn AGENT.md (frontmatter + body) into tool-specific files:

| Adapter | Output | Notes |
|---------|--------|-------|
| **Cursor** | `.cursor/rules/agent-from-agentmd.mdc` | Uses `description`, `globs`, `alwaysApply` in frontmatter |
| **Claude** | `claude.md` | Structured sections from frontmatter + body |
| **Copilot** | `.github/agents/agent.agent.md` | YAML frontmatter (`name`, `description`) + instructions from AGENT.md |

Templates: [adapters/](adapters/).

---

## Examples

| Project type | Path |
|--------------|------|
| WordPress | [examples/wordpress/AGENT.md](examples/wordpress/AGENT.md) |
| Node.js | [examples/nodejs/AGENT.md](examples/nodejs/AGENT.md) |
| Python | [examples/python/AGENT.md](examples/python/AGENT.md) |

---

## Tests and CI

- **Tests:** `pytest` for `agentmd lint` and `agentmd generate` (see [tests/](tests/)).
- **CI:** `.github/workflows/agentmd.yml` runs lint and tests, and validates that generated Cursor/Claude/Copilot files are non-empty and well-formed.

---

## Repository structure

```
.
├── spec/SPEC.md           # Formal specification
├── schema/
│   ├── agentmd.schema.json
│   └── agentmd.schema.yaml
├── adapters/              # Adapter templates (Cursor, Claude, Copilot)
├── examples/              # WordPress, Node.js, Python
├── src/agentmd/           # CLI and library
├── tests/
├── pyproject.toml
├── README.md
└── AGENT.md               # This project’s own AGENT.md
```

---

## License and contributing

- **License:** MIT (or as specified in the repository).
- **Contributing:** Open an issue or PR on [GitHub](https://github.com/rajanvijayan/agent.md). For schema or spec changes, please update both the JSON schema and [spec/SPEC.md](spec/SPEC.md).

---

## References

- [AGENTS.md](https://agents.md) — Simple, open format for agent instructions
- [Cursor Rules](https://cursor.com/docs/context/rules)
- [Claude Code / CLAUDE.md](https://claude.com/blog/using-claude-md-files)
- [GitHub Copilot Custom Agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
