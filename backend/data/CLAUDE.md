# Backend Data Instructions

This file intentionally mirrors the sibling instructions file in this directory. Keep both files in sync.

## Scope

Applies to `backend/data/`.

## Rules

- Treat this directory as runtime state, not hand-authored source code.
- Do not hand-edit generated cache or database files unless the task is explicitly about recovery or inspection.
- If a task requires committed fixtures, keep them clearly named and separate from live runtime state.
- Do not treat data files here as the canonical source of truth for backend behavior; source code and tests own that.
