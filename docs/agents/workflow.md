# Workflow

Feature changes follow three stages:

1. **Sketch** (`.agents/skills/sketch/SKILL.md`): turn an idea into a validated French spec in `~/.cache/mystgate/scratchpad/specs/<YYYY-MM-DD>-<subject>.md`, one question at a time.
2. **Plan** (`.agents/skills/plan/SKILL.md`): turn the validated spec into a small-task implementation plan in `~/.cache/mystgate/scratchpad/plans/<YYYY-MM-DD>-<subject>.md`.
3. **Execute** (`.agents/skills/execute/SKILL.md`): execute task by task with subagents, `.orchestration/<plan-name>/` ledger, per-task review, and final branch review.

## Shared Role Prompts & Per-Runtime Adapters

Full role instructions live once in `.agents/skills/execute/roles/{implementer,task-reviewer,fix-reviewer,branch-reviewer}.md` (plain Markdown, no frontmatter).

Per-runtime thin adapters delegate to those shared role prompts and are never placed under `.agents/agents/` and never symlinked:

- **Antigravity**: `.antigravity/agents/*.md` (discovered via `.agents/agents.json`)
- **Claude Code**: `.claude/agents/*.md` (skills symlinked via `.claude/skills -> ../.agents/skills`)
- **Codex**: `.codex/agents/*.toml`

| Role | Tier | Antigravity | Claude Code | Codex | Responsibilities |
|---|---|---|---|---|---|
| `implementer` | `standard` | `inherit` | `sonnet` | `medium` | TDD implementation, runs checks, fixes every failure and minor issue, stages without committing |
| `task-reviewer` | `standard` | `inherit` | `sonnet` | `medium` | Read-only review of staged task diff against brief and `AGENTS.md` |
| `fix-reviewer` | `fast` | `flash` | `haiku` | `low` | Read-only verification of each finding (`ADDRESSED`/`NOT ADDRESSED`) in fix diff |
| `branch-reviewer` | `strong` | `pro` | `opus` | `high` | Read-only cross-task review of full branch diff against spec, plan, and `AGENTS.md` |
