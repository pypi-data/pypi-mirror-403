# AGENT.md Specification

**Version:** 1.0.0  
**Status:** Draft  
**Repository:** https://github.com/rajanvijayan/agent.md

---

## 1. Purpose and Scope

AGENT.md is an **open, tool-agnostic standard** for defining AI agent project guidelines. It provides:

- A **predictable, machine-parseable** format that AI tools (Cursor, Claude, GitHub Copilot, Codex, etc.) can consume
- **Schema-validated** structured metadata (version, role, tech, rules, change-policy, output) for consistency and tooling
- A **human-friendly** Markdown body for setup, testing, conventions, and extended instructions
- **Single source of truth** that can be transformed into tool-specific formats (`.cursor/rules`, `claude.md`, `.github/agents/*.agent.md`)

AGENT.md complements [AGENTS.md](https://agents.md): AGENTS.md is free-form Markdown for simple agent instructions; AGENT.md adds a formal schema and frontmatter so projects can validate, extend, and generate tool-specific files from one definition.

---

## 2. Design Principles

1. **Tool-agnostic first** — The format does not assume Cursor, Claude, or Copilot. Adapters produce tool-specific output.
2. **Progressive disclosure** — Only `version` is required. All other frontmatter fields are optional. The body can be minimal or rich.
3. **Schema-validatable** — YAML frontmatter conforms to a JSON Schema so `agentmd lint` can validate before generation.
4. **Human-readable** — Authors edit Markdown and YAML; they do not need to write JSON or tool-specific syntax.
5. **Composable** — `extends` supports inheritance from a parent AGENT.md (e.g., org-wide or monorepo root).
6. **Compatible with AGENTS.md** — A project can use both: AGENTS.md for minimal, universal hints; AGENT.md when structured metadata and generation are desired.

---

## 3. Document Structure

An AGENT.md file consists of:

1. **Optional YAML frontmatter** — Between `---` delimiters at the top. Must be valid YAML. Parsed and validated against the AGENT.md schema.
2. **Optional Markdown body** — Everything after the frontmatter (or the whole file if no frontmatter). Standard Markdown. Conventional sections (e.g. `## Setup`, `## Testing`, `## Code Style`) are recommended but not enforced by the schema.

### 3.1 When frontmatter is present

- The file must start with `---` on the first line.
- The frontmatter ends at the next `---` on its own line.
- The body is the content after the closing `---`.

### 3.2 When frontmatter is absent

- The entire file is treated as the body. No structured metadata is available for schema validation or generation. Tools may still use the content as general instructions (AGENTS.md-style).

---

## 4. Frontmatter Schema

The following fields are defined for the YAML frontmatter. **Only `version` is required** when frontmatter is used. All other fields are optional.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | `string` | **Yes** | Schema version (e.g. `"1.0"`). Enables format evolution and validation. |
| `name` | `string` | No | Short, human-readable name for the agent profile. Useful for Copilot and UI. |
| `description` | `string` | No | One- or two-sentence description of the agent’s purpose. Used by Copilot `description` and similar. |
| `role` | `string` | No | Persona or role (e.g. `"Senior backend engineer"`, `"Documentation specialist"`). |
| `context` | `object` or `string` | No | Project/domain context. If object: `project`, `domain`, `audience` (all optional strings). |
| `priorities` | `array of strings` | No | Ordered list of priorities (e.g. `["correctness", "security", "performance"]`). |
| `tech` | `object` | No | Technology constraints. See [4.1](#41-tech-object). |
| `rules` | `array` | No | Rule items. See [4.2](#42-rules-array). |
| `change-policy` | `object` | No | Git and change workflow. See [4.3](#43-change-policy-object). |
| `output` | `object` | No | Output and documentation expectations. See [4.4](#44-output-object). |
| `extends` | `string` | No | Path to a parent AGENT.md (e.g. `"../AGENT.md"` or `"https://..."`). Parent fields are deep-merged; child overrides parent. |
| `globs` | `array of strings` or `string` | No | File patterns (e.g. `["*.ts", "src/**"]`) for tools that support path-scoped rules. |
| `alwaysApply` | `boolean` | No | If `true`, instructs generators to mark the rule as “always apply” where supported (e.g. Cursor). |

Unrecognized keys in the frontmatter **MUST** be preserved by tooling when rewriting or generating; they **MAY** be ignored for validation if not in the schema.

### 4.1 `tech` object

| Key | Type | Description |
|-----|------|-------------|
| `stack` | `array of strings` | Main technologies (e.g. `["Node.js", "React", "PostgreSQL"]`). |
| `versions` | `object` | Version constraints. Keys are tech names; values are strings (e.g. `node: ">=20"`, `python: "3.11"`). |
| `constraints` | `array of strings` | Free-form constraints (e.g. `"No `any` in TypeScript"`, `"Python 3.11+ only"`). |

### 4.2 `rules` array

Each item is either:

- A **string** — Plain instruction (e.g. `"Use TypeScript strict mode"`).
- An **object** with:
  - `description` (string, required): The rule text.
  - `globs` (array of strings, optional): File patterns for this rule.
  - `id` (string, optional): Stable identifier for reference.

### 4.3 `change-policy` object

| Key | Type | Description |
|-----|------|-------------|
| `branching` | `string` | Branch naming (e.g. `"feature/*"`, `"main"`). |
| `commits` | `string` | Commit style (e.g. `"conventional"`, `"linear"`). |
| `reviews` | `string` or `boolean` | Review requirements (`"required"`, `true`, or `false`). |
| `breaking` | `string` | How to handle breaking changes (e.g. `"major version"`, `"migration guide"`). |

### 4.4 `output` object

| Key | Type | Description |
|-----|------|-------------|
| `formats` | `array of strings` | Expected output formats (e.g. `["markdown", "code"]`). |
| `conventions` | `array of strings` | Conventions (e.g. `"JSDoc for public APIs"`, `"ADR for architecture"`). |
| `docs` | `boolean` | Whether the agent should maintain or create docs. |

---

## 5. Markdown Body

The body uses standard CommonMark. No extra structure is mandated. These sections are **conventional** and recommended for interoperability:

- `## Setup` — Install, environment, and run commands.
- `## Testing` — How to run tests, coverage, and CI.
- `## Code Style` — Linting, formatting, and naming.
- `## Architecture` — Patterns, layers, and conventions.
- `## Security` — Safeguards and sensitive data.
- `## Deployment` — Build, deploy, and release steps.

Adapters **MAY** map these to tool-specific sections. The body is passed through to generated instruction files, possibly with tool-specific wrappers.

---

## 6. File Location and Precedence

- **Default location:** `AGENT.md` at the repository root.
- **Nested files:** `AGENT.md` may appear in subdirectories. Tool-specific behavior for “nearest” or “merge” is defined by each adapter.
- **Naming:** The canonical name is `AGENT.md`. Implementations may also support `AGENT.yaml` (YAML-only, no body) as defined in an extension of this spec.

---

## 7. Extends and Inheritance

When `extends` is set:

1. The parent AGENT.md is resolved (local path or URL).
2. Frontmatter is **deep-merged**: parent base, child overrides. Arrays are overridden entirely by the child when the same key exists.
3. Body: the child body **replaces** the parent body by default. A future extension could define `merge: append` or similar.

If the parent cannot be resolved, tooling **SHOULD** warn and continue with only the current file.

---

## 8. Relationship to Other Formats

| Format | Purpose | Relationship |
|--------|---------|--------------|
| **AGENTS.md** | Simple, free-form agent instructions; no schema. | AGENT.md extends this idea with schema and generation. Projects can use both. |
| **.cursor/rules** | Cursor-specific rules with `description`, `globs`, `alwaysApply`. | Produced by the Cursor adapter from AGENT.md. |
| **claude.md** | Claude project instructions; plain Markdown. | Produced by the Claude adapter from AGENT.md frontmatter + body. |
| **.github/agents/*.agent.md** | Copilot custom agents; YAML frontmatter + body. | Produced by the Copilot adapter from AGENT.md. |

---

## 9. Versioning

- The `version` in the frontmatter refers to the **AGENT.md schema version** (e.g. `1.0`), not the project version.
- This spec uses SemVer for the document. Backwards-incompatible schema changes will bump the major version; new optional fields typically the minor.

---

## 10. Conformance

- **Valid AGENT.md:** (a) Optional valid YAML frontmatter that conforms to the schema when present, and (b) optional UTF-8 Markdown body.
- **Schema:** The normative schema is `schema/agentmd.schema.json`. The YAML frontmatter, when parsed to JSON, must validate against it.
- **Adapters:** Adapters are non-normative. They should document how they map AGENT.md to each tool’s format.

---

## Appendix A. Example (Minimal)

```markdown
---
version: "1.0"
---

## Setup
- `npm install`
- `npm run dev`
```

---

## Appendix B. Example (Full)

```markdown
---
version: "1.0"
name: backend-agent
description: Backend development for the API service
role: Senior backend engineer
context:
  project: Order API
  domain: e-commerce
priorities:
  - correctness
  - security
  - performance
tech:
  stack: [Node.js, TypeScript, PostgreSQL]
  versions: { node: ">=20", typescript: "~5.3" }
  constraints:
    - "No `any`; use `unknown` when needed"
rules:
  - "Use REST resource naming from docs/API.md"
  - description: "Validate request body with Zod in route handlers"
    globs: ["src/routes/**/*.ts"]
change-policy:
  branching: "feature/*"
  commits: "conventional"
  reviews: "required"
output:
  docs: true
  conventions: ["OpenAPI for new endpoints"]
---

## Setup
- `pnpm install`
- `cp .env.example .env` and set `DATABASE_URL`
- `pnpm db:migrate`

## Testing
- `pnpm test` — unit and integration
- `pnpm test:e2e` — against `test` DB

## Code Style
- ESLint + Prettier; `pnpm lint`
- Pre-commit: `lint-staged`
```
