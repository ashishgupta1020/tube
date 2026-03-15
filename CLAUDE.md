# Tube Project Instructions

This file intentionally mirrors the sibling instructions file in this directory. Keep both files in sync.

## Scope

Applies to the repository root unless a deeper instruction file overrides it.

## Project Shape

- `backend/` contains the dependency-light Python HTTP server, TfL integration, normalization pipeline, and unit/integration tests.
- `frontend/` contains static `index.html`, `app.js`, `styles.css`, and vendored MapLibre assets served by the backend.
- `docs/` contains product and external API reference docs for the current project scope.
- `plans/` contains design plans and implementation notes; useful context, but some content may describe future work.

## Commands

- Run the app: `python3 -m backend.main`
- Run tests: `python3 -m unittest discover backend/tests -v`

## Global Rules

- Keep the app dependency-light. Do not add a frontend build step, JS framework, or Python web framework unless explicitly requested.
- Keep the backend as the only boundary to TfL. Frontend code should consume backend endpoints, not call TfL directly.
- Preserve the current read-only backend shape unless the change intentionally updates backend, frontend, tests, and docs together.
- Favor focused changes that fit the existing directory boundaries instead of broad rewrites.
- Add or update docstrings when introducing new classes or functions anywhere in the project.
- Prefer the simplest implementation that satisfies the change cleanly.
- Do not hesitate to refactor existing code when the refactor is needed to make the resulting implementation simpler.
- Treat `docs/` and `plans/` as part of the product surface. Update them when behavior, scope, or architectural direction changes.

## Current Contract

- Public endpoints currently include `GET /api/map/stations` and `GET /health`.
- The map frontend expects a `v1` payload and uses backend-provided camera and bounds values.
- The map should stay north-up, map-first, and responsive on desktop and mobile.

## Done Criteria

- Run the relevant tests for the area you changed, or state why tests were not run.
- If API or UI behavior changed, update the matching docs and plans in the same change.
