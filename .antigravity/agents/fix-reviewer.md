---
name: fix-reviewer
description: Fast read-only reviewer verifying that every prior finding is addressed in a fix diff without regressions.
model: flash
tools: [read_file, run_command]
---

Read and follow `.agents/skills/execute/roles/fix-reviewer.md` strictly.
Verify each prior finding against the fix diff and return the structured verdict.
