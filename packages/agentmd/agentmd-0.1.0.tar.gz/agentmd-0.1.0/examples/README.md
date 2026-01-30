# AGENT.md Examples

Example `AGENT.md` files for different project types. Use `agentmd lint <path>` to validate and `agentmd generate` from each directory to produce tool-specific files.

| Project type | Path | Notes |
|--------------|------|-------|
| **WordPress** | [wordpress/AGENT.md](wordpress/AGENT.md) | Themes, plugins, PHP, WP APIs, security |
| **Node.js** | [nodejs/AGENT.md](nodejs/AGENT.md) | TypeScript, pnpm, REST, OpenAPI |
| **Python** | [python/AGENT.md](python/AGENT.md) | Python 3.11+, ruff, pytest, Pydantic |

Each example includes `version`, `role`, `context`, `priorities`, `tech`, `rules`, `change-policy`, and `output`, plus conventional body sections (Setup, Testing, Code Style, Security, Deployment).
