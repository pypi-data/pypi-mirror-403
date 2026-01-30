---
version: "1.0"
name: nodejs-agent
description: AI agent guidelines for Node.js and TypeScript projects
role: Senior Node.js / full-stack engineer
context:
  project: Node.js application or library
  domain: web, API, CLI
  audience: Developers and DevOps
priorities:
  - correctness
  - security
  - performance
tech:
  stack: [Node.js, TypeScript, npm/pnpm/yarn]
  versions: { node: ">=20", typescript: "~5.3" }
  constraints:
    - "No `any`; use `unknown` when type is truly dynamic"
    - "Prefer async/await over raw Promises"
    - "Use `node:` prefix for built-in modules"
rules:
  - "Use strict TypeScript; `strict: true` in tsconfig"
  - "Prefer pnpm; lockfile must be committed"
  - "REST: follow resource naming and HTTP semantics from OpenAPI or project docs"
  - description: "Validate env and config at startup with Zod or a similar schema"
    globs: ["src/**/*.ts", "config/**/*.ts"]
change-policy:
  branching: "feature/*"
  commits: "conventional"
  reviews: "required"
  breaking: "major version bump; document in CHANGELOG"
output:
  docs: true
  conventions: ["JSDoc for public APIs", "README for packages", "OpenAPI for REST"]
---

## Setup
- `pnpm install` (or `npm ci` / `yarn install` per project)
- `cp .env.example .env` and set required vars
- `pnpm db:migrate` or equivalent if the project uses DB migrations

## Testing
- Unit/integration: `pnpm test` (Vitest, Jest, or Node tap)
- E2E: `pnpm test:e2e` when defined
- Lint: `pnpm lint` before committing

## Code Style
- ESLint + Prettier; config in repo root
- Pre-commit: `lint-staged` or `husky` if configured
- Naming: camelCase (code), kebab-case (files, packages)

## Architecture
- Prefer dependency injection or factory functions over global state
- Use a consistent structure: `src/`, `lib/`, or framework defaults (Next.js, Nest, etc.)

## Security
- Never commit secrets; use `process.env` and `.env` (gitignored)
- Validate and sanitize user input; use parameterized queries for SQL
- Keep deps updated: `pnpm audit`, Dependabot

## Deployment
- Build: `pnpm build`
- Run: `node dist/main.js` or `pnpm start`; use `NODE_ENV=production`
