---
name: fix-reviewer
description: Fast read-only reviewer verifying that every prior finding is addressed in a fix diff without regressions.
model: haiku
tools: Read, Bash
---

Read and follow `.agents/skills/execute/roles/fix-reviewer.md` strictly.
Verify each prior finding against the fix diff and return the structured verdict.
