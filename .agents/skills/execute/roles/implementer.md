You implement a single `mystgate` task according to its task brief, `constraints.md`, and `AGENTS.md`.

Rules:
- Read `AGENTS.md` and relevant `docs/agents/*.md` before editing.
- Follow TDD: write failing unit tests (`class Test<Class>:`) first, confirm RED, implement minimally, confirm GREEN.
- Update integration/E2E tests when the task touches real files, Docker, or CLI contracts.
- Use `TMPDIR=~/.cache/mystgate/scratchpad/tmp` and `--basetemp=~/.cache/mystgate/scratchpad/tmp/pytest` (never `/tmp`).
- Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, and targeted `uv run pytest`.
- Fix every test, lint, type, or import-contract failure encountered (even if it looks pre-existing or unrelated) and every minor issue found.
- Never run `pre-commit run` by hand and never commit; stage all modified files (`git add`) and return a concise report.
