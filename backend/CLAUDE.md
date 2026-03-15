# Backend Instructions

This file intentionally mirrors the sibling instructions file in this directory. Keep both files in sync.

## Scope

Applies to `backend/` unless a deeper instruction file overrides it.

## Commands

- Run the backend: `python3 -m backend.main`
- Run backend tests: `python3 -m unittest discover backend/tests -v`

## Conventions

- Stay stdlib-first. Do not introduce Flask, FastAPI, ORM layers, or background job frameworks unless explicitly requested.
- Preserve the current module boundaries: `controllers`, `routes`, `services`, `integrations`, `normalizers`, `repositories`, `models`, and `config`.
- Keep the backend as a stable boundary over TfL. Normalize upstream data before exposing it to the frontend.
- Return deterministic response shapes and explicit HTTP status codes. Avoid leaking raw upstream payloads through public routes.
- Prefer small, testable functions for normalization, bounds calculation, routing, and response formatting.
- Keep secrets in environment variables. Do not hardcode TfL credentials or other secrets into source files.

## Change Expectations

- If `GET /api/map/stations` changes, update frontend handling, backend tests, and the relevant docs in the same change.
- If routing or startup changes, verify the backend still serves the static frontend and `GET /health`.
