---
name: sketch
description: >-
  Turn an idea of the owner into a validated spec for mystgate, one question at a time,
  before any plan or code. Use when the owner wants to add, change or remove a feature,
  or says "esquisse", "sketch", "spec" or "design".
---

# Sketch (`mystgate`)

Turn a rough idea into a concise, validated specification before planning or coding.

## Steps

1. **Understand**:
   - Read the relevant modules under `mystgate/` and the matching guides in `docs/agents/`.
   - Ask **one question at a time** with concrete options and a clear recommendation.
   - Stop asking once every section of the spec can be written without guessing.
2. **Write the spec**:
   - Write in French to `~/.cache/mystgate/scratchpad/specs/<YYYY-MM-DD>-<subject>.md` (never inside the repository).
   - Required sections:
     - `## Intention`
     - `## Objectifs / Non-objectifs / Anti-objectifs`
     - `## Ce qui reste / Ce qui part / Ce qui arrive`
     - `## Erreurs et codes de sortie`
     - `## État local, secrets et sécurité`
     - `## Documents et fichiers à mettre à jour`
   - Mark owner-confirmed decisions `[owner]` and proposed defaults `[proposé]`.
3. **Validate**:
   - Resolve every `[proposé]` item one question at a time.
   - Once validated, propose moving to the `plan` skill.
