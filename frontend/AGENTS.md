# Frontend Instructions

This file intentionally mirrors the sibling instructions file in this directory. Keep both files in sync.

## Scope

Applies to `frontend/` unless a deeper instruction file overrides it.

## Commands

- Run the full app through the backend: `python3 -m backend.main`

## Conventions

- Keep the frontend build-free. Edit the static assets directly; do not add bundlers, transpilers, or frameworks unless explicitly requested.
- Stay aligned with the current vanilla JS style in `app.js`. New code should work without a compile step.
- Treat the backend as the only data source. Frontend code should fetch backend endpoints and validate the response before rendering.
- Keep the map as the primary surface: responsive, north-up, safe-area aware, and usable on desktop and mobile.
- Prefer a single GeoJSON source and map layer for station rendering rather than large sets of DOM markers.
- Preserve the existing visual direction: map-first layout, restrained palette, and compact overlays.

## Change Expectations

- If the frontend starts depending on new API fields, add the backend support, docs updates, and test coverage in the same change.
- If you touch third-party assets under `frontend/vendor/`, treat that as an intentional vendor update, not a routine edit.
