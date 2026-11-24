---
name: task-reviewer
description: Read-only reviewer checking a staged mystgate task diff against its brief and AGENTS.md.
model: inherit
tools: [read_file, run_command]
---

Read and follow `.agents/skills/execute/roles/task-reviewer.md` strictly.
Review the provided diff package and return the structured verdict.
