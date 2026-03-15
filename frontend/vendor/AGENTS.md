# Vendored Asset Instructions

This file intentionally mirrors the sibling instructions file in this directory. Keep both files in sync.

## Scope

Applies to `frontend/vendor/`.

## Rules

- Treat files here as vendored third-party assets.
- Avoid editing these files unless the task is explicitly a vendor patch or upgrade.
- If you do update a vendored asset, keep the related JS and CSS files compatible and note the upstream source in the change summary.
- Prefer making project-specific behavior changes in first-party frontend code rather than patching vendor files.
