---
name: execute
description: >-
  Execute a mystgate plan task by task with subagents, one implementer per task, a
  reviewer after each, every finding fixed, and a review of the whole branch at the end.
  Use when the owner gives a plan and asks to run it (this is the owner's explicit request
  for subagents).
---

# Execute (`mystgate`)

Run an implementation plan task by task using isolated subagents and strict review gates.

Role instructions live once in `.agents/skills/execute/roles/{implementer,task-reviewer,fix-reviewer,branch-reviewer}.md`. Runtime adapters live in `.antigravity/agents/` (via `.agents/agents.json`), `.claude/agents/`, and `.codex/agents/`. Any other runtime reads `.agents/skills/execute/roles/<role>.md` directly and maps the tier (`fast`, `standard`, `strong`) to its own model selector.

## Setup

1. Create `.orchestration/<plan-name>/` (gitignored) with `progress.md` and `constraints.md` (recording `TMPDIR=~/.cache/mystgate/scratchpad/tmp`, `--basetemp=~/.cache/mystgate/scratchpad/tmp/pytest`, no `Co-Authored-By`, never running `pre-commit run` by hand, and the zero-ignored-failures rule).
2. Record `<first base>` (`git rev-parse HEAD`).

## Per-Task Loop

1. Generate the task brief:
   ```bash
   bash .agents/skills/execute/scripts/task-brief <plan> <id> .orchestration/<plan-name>
   ```
2. Dispatch `implementer` (`standard` tier; `strong` for heavy tasks) with the brief and `constraints.md`. The implementer works TDD, fixes every test/lint/type/import failure (even seemingly unrelated ones) and minor issues, stages changes without committing, and reports.
3. Build the review diff package:
   ```bash
   bash .agents/skills/execute/scripts/review-package <base> index .orchestration/<plan-name>
   ```
4. Dispatch `task-reviewer` (`standard` tier, read-only) on the diff package against the brief and `AGENTS.md`.
5. For any finding (including minor issues), run a fix loop with `implementer` -> `fix-reviewer` (`fast` tier, read-only) until approved (escalate to `strong` after 3 rounds, controller rules after 5).
6. Verify `git write-tree` matches the reviewed index tree and commit with the task's Conventional Commit message.

## End of Plan

1. Run remaining definition-of-done checks: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, `uv run pytest`, `uv run pytest tests/integration/`, and `uv run --isolated --no-dev --group test mystgate --help && uv run --isolated --no-dev --group test pytest`.
2. Build full branch diff with `review-package <first base> HEAD .orchestration/<plan-name>` and dispatch `branch-reviewer` (`strong` tier, read-only).
3. Fold any final fixes with `git commit --fixup=<sha>` and `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <first base>`.
4. Report completion in French without pushing.
