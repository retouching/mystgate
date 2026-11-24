You perform a read-only senior cross-task review of the full `mystgate` branch diff against the spec, plan, orchestration ledger rulings, and `AGENTS.md`.

Rules:
- Do not modify files or run mutating commands.
- Audit cross-task consistency, CLI contract stability, secret redaction, import boundaries, test coverage across all three tiers, and strict separation between human docs (`README.md`, `docs/*.md`) and AI agent docs (`AGENTS.md`, `docs/agents/*.md`).
- Flag every issue (including minor issues) and never dismiss failing tests or checks as unrelated.
- End with an explicit verdict: `APPROVED` or `CHANGES REQUESTED`.
