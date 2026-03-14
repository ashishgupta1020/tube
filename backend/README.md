# Backend

Dependency-light Python backend for the v1 London rail map.

Current implementation:

- stdlib HTTP server
- TfL stop-point client via `urllib`
- station normalization and deduplication
- in-memory dataset cache
- background refresh job
- one public endpoint at `GET /api/map/stations`

Run locally:

```bash
python3 -m backend.main
```

Useful environment variables:

- `BACKEND_HOST`
- `BACKEND_PORT`
- `TFL_APP_KEY`

Tests:

```bash
python3 -m unittest discover backend/tests -v
```
