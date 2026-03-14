# Map Backend Design Plan

## Summary

This plan defines the backend architecture for the v1 London rail map. The backend's job is to fetch scoped TfL rail station data, normalize it to station-level map points, cache it, and serve a stable frontend-facing API that can render a city-centre map with one marker per station.

For v1, the backend should stay intentionally thin:

- one read-only map API
- one TfL integration layer
- one station normalization pipeline
- one cache-backed station dataset

The backend does not need user accounts, writes, live arrivals, route overlays, or map-specific business workflows yet.

## Goals

- Return one canonical station record per scoped station for map rendering.
- Hide TfL stop-point complexity from the frontend.
- Reduce direct frontend dependence on TfL response shape and rate limits.
- Make the map load from a stable backend contract, even if TfL is slow or temporarily unavailable.
- Keep the design extensible for later additions like station detail, line overlays, and arrivals.

## Architecture

### 1. Backend Role

The backend should act as a small boundary service between the frontend and TfL:

- pulls raw station data from TfL for `tube,dlr,overground,elizabeth-line`
- normalizes and deduplicates the stop-point data into station-level map points
- caches the normalized dataset
- serves a frontend-focused API for the map

The frontend should not call TfL directly for the v1 map.

### 2. Service Shape

Use a single application service with these internal modules:

- `tflClient`
  - handles outbound requests to TfL
  - owns auth, timeouts, retries, and response validation
- `stationNormalizer`
  - converts raw TfL stop points into canonical station map entities
  - deduplicates multi-mode and interchange stations
- `stationRepository`
  - reads and writes the normalized station dataset from cache or persistence
- `mapService`
  - returns the current station dataset and map metadata to HTTP handlers
- `mapController`
  - exposes the read-only API endpoint consumed by the frontend

For v1, these can all live inside one deployable backend service.

### 3. Data Flow

The v1 data flow should be:

1. Backend requests TfL stop points for the scoped rail modes.
2. Raw stop-point payload is validated.
3. Normalization converts raw stop points into canonical station entities.
4. Normalized dataset is stored in cache.
5. Frontend requests the backend map endpoint.
6. Backend returns the cached normalized station dataset plus static camera defaults.

### 4. Sync Strategy

Use a server-side refresh model rather than fetching TfL on every frontend request.

- refresh the scoped station dataset on a fixed interval
- also allow lazy bootstrap on first request if no cache exists yet
- apply a dataset TTL to both the in-memory cache and persisted record metadata
- serve the last good dataset if a scheduled refresh fails
- never block the frontend on a fresh TfL fetch if cached data already exists

Recommended default for v1:

- dataset TTL: 24 hours
- refresh required once cached data is older than 24 hours
- refresh interval: every 24 hours
- outbound TfL timeout: 5 seconds
- retry count: 2 retries on transient failure
- stale-data tolerance: 7 days before the dataset is considered unusable

Station data is relatively static, so freshness is much less important than stability.

## Source Data

### TfL Endpoint

Primary upstream source:

- `GET /StopPoint/Mode/tube,dlr,overground,elizabeth-line`

This endpoint should be treated as the canonical source for broad station coverage in the scoped network.

### Upstream Constraints

- TfL auth should be handled server-side with `app_key`.
- The backend must assume TfL can rate-limit, timeout, or return broader stop-point shapes than the frontend needs.
- TfL responses may include platform-level or duplicate entities that are not appropriate as map markers.

## Normalized Backend Model

The backend should expose a stable station-level shape and keep TfL-specific noise internal.

### Canonical Station Entity

```ts
type RailMode = "tube" | "dlr" | "overground" | "elizabeth-line";

type MapStation = {
  id: string;
  name: string;
  location: {
    lat: number;
    lon: number;
  };
  modes: RailMode[];
};
```

### Normalization Rules

- Use one entity per station, not per platform.
- Prefer stop-area or station-level records over child/platform records when both exist.
- Deduplicate stations that appear multiple times across scoped modes.
- Keep TfL station IDs stable when a clear station-level ID is available.
- If multiple raw records represent the same station, merge their scoped modes into one `modes` array.
- Drop records without valid latitude or longitude.
- Drop records outside the scoped rail modes.
- Sort the final list deterministically by station name, then ID, before storing and returning it.

### Normalization Output

The stored normalized dataset should contain:

- `stations`: array of `MapStation`
- `updatedAt`: timestamp of the last successful refresh
- `expiresAt`: timestamp derived from the 24-hour TTL
- `source`: static identifier such as `tfl-stop-point-mode`
- `version`: response schema version for the frontend contract

## Public API Contract

### `GET /api/map/stations`

This should be the only required v1 map endpoint.

Response shape:

```ts
type MapStationsResponse = {
  version: "v1";
  generatedAt: string;
  camera: {
    center: {
      lat: number;
      lon: number;
    };
    zoom: number;
    maxBounds: {
      southWest: { lat: number; lon: number };
      northEast: { lat: number; lon: number };
    };
  };
  stations: Array<{
    id: string;
    name: string;
    location: {
      lat: number;
      lon: number;
    };
    modes: Array<"tube" | "dlr" | "overground" | "elizabeth-line">;
  }>;
};
```

### Endpoint Behavior

- Returns the latest normalized station dataset from backend cache or persistence.
- Treats datasets older than the 24-hour TTL as expired and triggers a refetch requirement before they can be refreshed in place.
- Includes static camera defaults for the frontend's city-centre initial view.
- Includes computed max bounds so the frontend can constrain panning to the network region.
- Must not proxy raw TfL response bodies.
- Must return deterministic field names and ordering across requests when data is unchanged.

### HTTP Semantics

- `200` with dataset when cache or persisted storage contains a usable station dataset.
- `503` only if no usable station dataset exists and the backend cannot build one.
- `Cache-Control` should allow short client-side caching, but the backend remains the main cache boundary.

Recommended default headers:

- `Cache-Control: public, max-age=300, stale-while-revalidate=60`

## Camera and Bounds Responsibilities

The frontend map starts from a city-centre camera, but the backend should still own the canonical geographic envelope of the dataset.

- Backend should store and return a static default camera for central London.
- Backend should compute max bounds from the normalized station dataset with small padding.
- Backend should not attempt to calculate dynamic "best fit" initial view for v1.

Recommended v1 defaults:

- center: central London
- zoom: a city-centre zoom suitable for first-load orientation
- bearing: implicitly north-up by omitting rotation data

The exact lat/lon/zoom constants should be set once in code and exposed through the map response.

## Storage and Caching

### V1 Choice

Use in-memory cache for active reads and SQLite as the persistence layer on disk.

Rationale:

- the dataset is modest
- the API is read-only
- refresh frequency is low
- SQLite gives us durable local persistence without introducing external infrastructure
- the same persistence choice can grow with later backend features

### Required Behavior

- Keep the active normalized dataset in memory for low-latency reads.
- Persist the last good dataset in SQLite so restarts can recover quickly.
- On startup, load the latest persisted dataset from SQLite before attempting a fresh TfL refresh.
- Store TTL metadata alongside the persisted dataset so expiry rules are consistent across memory and disk.
- Replace the in-memory dataset only after a full refresh and normalization succeeds.

### Files

The implementation should use a backend-owned SQLite database file such as:

- `data/app.db`

This file should be treated as runtime state, not hand-edited source content.

## Resilience and Error Handling

- Validate TfL responses before normalization.
- Fail refreshes atomically; never partially update the stored dataset.
- Log refresh attempts, failure reasons, record counts before and after normalization, and last-success timestamp.
- If TfL is unavailable but a prior dataset exists, keep serving the stale dataset.
- If the cached dataset is older than the 24-hour TTL, mark it expired and require a refetch attempt before renewing freshness metadata.
- If the normalized station list becomes suspiciously small compared with the previous good persisted dataset, reject the refresh and retain the prior dataset.

Recommended guardrail:

- reject refresh if normalized station count drops by more than 25% versus the last successful persisted dataset unless explicitly overridden

## Security

- Keep the TfL `app_key` server-side only.
- Do not expose raw upstream credentials or raw TfL response metadata to the frontend.
- Apply outbound request timeouts and a narrow allowlist of TfL base URLs.
- Expose only read-only public endpoints for the v1 map.

## Observability

The backend should emit basic operational signals from day one:

- last successful TfL refresh timestamp
- refresh duration
- refresh success/failure count
- normalized station count
- API response count and latency for `/api/map/stations`
- persisted dataset load success/failure on startup

These can start as structured logs if metrics infrastructure does not exist yet.

## Testing Plan

### Unit Tests

- normalize a station-level record into one `MapStation`
- merge duplicates across scoped modes into one station entity
- ignore platform-level or child stop-point records when a station-level record exists
- reject records without coordinates
- preserve deterministic output ordering
- compute padded max bounds correctly from the normalized station list

### Integration Tests

- refresh pipeline from mocked TfL payload to cached normalized dataset
- startup behavior with persisted SQLite data present and TfL unavailable
- API response shape for `GET /api/map/stations`
- stale persisted dataset serving when refresh fails
- bootstrap behavior when no cache exists yet

### Contract Tests

- response schema remains stable for frontend consumption
- `modes` only contains scoped values
- `camera` fields are always present

## Non-Goals For V1

- no station search endpoint
- no station detail endpoint
- no live arrivals endpoint
- no line status endpoint
- no route geometry endpoint
- no user-specific state
- no database-backed editing or admin tooling

Those can be added later without changing the role of the map station dataset service.

## Assumptions

- There is no existing backend stack in the repo, so this plan chooses a simple service-oriented architecture with explicit defaults.
- The frontend should receive station-level data from our backend, not directly from TfL.
- The v1 map only needs read-only station and camera data.
- The city-centre initial camera is a product decision; dataset-wide bounds are only for pan limits, not initial fit.
