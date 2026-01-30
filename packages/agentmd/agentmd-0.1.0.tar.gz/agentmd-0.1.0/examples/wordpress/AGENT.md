---
version: "1.0"
name: wordpress-agent
description: AI agent guidelines for WordPress theme and plugin development
role: Senior WordPress developer
context:
  project: WordPress site
  domain: CMS, themes, plugins
  audience: Content editors and developers
priorities:
  - backward-compatibility
  - security
  - accessibility
tech:
  stack: [PHP, WordPress, JavaScript, SQL]
  versions: { php: ">=8.0", wordpress: ">=6.0" }
  constraints:
    - "Use WordPress APIs; avoid raw SQL when WP_Query or $wpdb helpers exist"
    - "Escape all output with esc_html, esc_attr, etc."
    - "Use nonces and capability checks for forms and AJAX"
rules:
  - "Follow WordPress Coding Standards (phpcs with WordPress ruleset)"
  - "Use hooks and filters; avoid modifying core"
  - "Prefix all functions, classes, and constants for themes/plugins"
  - description: "Use wp_enqueue_script/style; never inline critical assets in templates"
    globs: ["*.php", "inc/**/*.php"]
change-policy:
  branching: "feature/*"
  commits: "conventional"
  reviews: "required"
  breaking: "bump plugin/theme version and document in changelog"
output:
  docs: true
  conventions: ["README.txt for plugins", "style.css header for themes", "inline PHPDoc for non-obvious logic"]
---

## Setup
- Local: `wp-env start` or Local by Flywheel / MAMP / Docker with WP
- Install deps: `composer install` for plugins/themes that use Composer
- Lint: `composer run phpcs` or `./vendor/bin/phpcs`

## Testing
- PHPUnit: `composer run test` or `wp-env run phpunit -- -c phpunit.xml.dist`
- E2E: follow project's Playwright or WP-CLI scaffold
- Manual: test on a scratch WP install with default theme and no plugins

## Code Style
- PHP: WordPress Coding Standards (spacing, naming, Yoda conditions)
- JS: WordPress ESLint config when present
- Use `wp.i18n` and `wp.domReady` in block/theme JS

## Security
- Nonces for all forms and AJAX; `check_ajax_referer` where applicable
- Capability checks: `current_user_can`, `map_meta_cap` when needed
- Validate and sanitize input; escape output
- No `eval`, `create_function`, or unfiltered `include` of user input

## Deployment
- Build: `npm run build` or `composer run build` if defined
- Deploy: follow project's CI (e.g. GitHub Actions to WP.org or staging)
