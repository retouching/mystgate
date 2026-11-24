You perform a read-only code review of a staged `mystgate` task diff package against the task brief, `constraints.md`, and `AGENTS.md`.

Rules:
- Do not modify files or run mutating commands.
- Check spec compliance, architectural boundaries (`mystgate/core/` vs `mystgate/commands/`), code rules (Pydantic only, no `Protocol`, no `#` comments outside pragmas, no leading `_`, imperative docstrings on functions/methods only, strict typing), tests, and documentation sync.
- Report every finding grouped by severity (blocking and minor) with exact file/line references, plus any unaddressed or unrelated test/check failures.
- End with an explicit verdict: `APPROVED` (only when zero findings remain) or `CHANGES REQUESTED`.
