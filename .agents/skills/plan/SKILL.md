---
name: plan
description: >-
  Turn a validated mystgate spec into an implementation plan of small tasks, each with its
  files, interfaces, tests and commit, that subagents can execute. Use after the sketch
  skill, or when the owner asks for a plan.
---

# Plan (`mystgate`)

Turn one validated specification into a single step-by-step implementation plan.

## Rules

- One spec -> one plan covering the whole spec; one active plan at a time.
- Write in French to `~/.cache/mystgate/scratchpad/plans/<YYYY-MM-DD>-<subject>.md` (never inside the repository).
- Keep structural headings in English so `.agents/skills/execute/scripts/task-brief` parses them:
  - `**Goal:**`
  - `**Architecture:**`
  - `**Spec:**`
  - `## Global Constraints`
  - `## Review Focus`
  - `### Task <id>: <title>`
- Each task lists:
  - **Files** (exact paths to create/edit/delete)
  - **Interfaces** (`Consumes` / `Produces`)
  - **Steps** (TDD: write failing unit test -> RED -> implement -> GREEN with `uv run pytest tests/unit/<file>`, plus `ruff`, `mypy`, `lint-imports`)
  - **Commit** (Conventional Commit in English, no attribution footer)
- Final task updates docs (`README.md`, `docs/usage.md`, `docs/configuration.md`, `docs/docker.md`, `docs/mysterium-api.md`, `.env.example`, `AGENTS.md`, `docs/agents/*.md`), runs changed integration/E2E tests, full unit suite, and `--isolated --no-dev --group test` checks.
