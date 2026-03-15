# Map Frontend Design Plan

## Summary

This plan defines the v1 frontend for the London rail map. It is based on:

- the product and interaction goals in [docs/map-design.md](/Users/shaynaarora/sandbox/tube/docs/map-design.md)
- the intended backend architecture in [plans/map/backend-design.md](/Users/shaynaarora/sandbox/tube/plans/map/backend-design.md)
- the backend that is currently implemented under [backend](/Users/shaynaarora/sandbox/tube/backend)

The frontend should treat the backend as the only map data source, render a navigable London map, and display one visible marker per normalized station. The first version should optimize for reliability, clarity, and a clean extension path for later station selection and line overlays.

## Backend Reality The Frontend Should Design Against

The implemented backend currently exposes:

- `GET /api/map/stations`
- `GET /health`

The map endpoint returns:

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

Important implementation details from the current backend:

- the frontend should use `generatedAt` as its only freshness timestamp
- the backend already computes canonical `maxBounds`
- the backend already deduplicates interchange stations and merges `modes`
- the backend can return `503` when no usable dataset exists
- the backend uses `Cache-Control: public, max-age=300, stale-while-revalidate=60`

Important gaps between the backend design doc and the current implementation:

- no persisted SQLite cache yet; only in-memory cache exists
- no `updatedAt`, `expiresAt`, or `source` fields are returned to the client
- no dedicated station detail endpoint exists yet

The frontend should not invent dependencies on fields or endpoints that are not implemented.

## Frontend Goals

- Render a full-screen-feeling primary map surface for London rail exploration.
- Fetch station data from the backend once per page load and render every station as a map point.
- Use the backend-provided camera defaults and bounds as the canonical initial framing.
- Keep the interaction model minimal: pan, zoom, north-up orientation, and visible controls.
- Leave a clean path for later station selection, side panels, line overlays, and arrivals.

## Recommended Frontend Architecture

### 1. Page Composition

The v1 map page should have three UI layers:

1. a map canvas that owns the full interactive surface
2. a small overlay header for title and dataset freshness
3. transient overlays for loading, empty, and error states

The map itself should remain the dominant element. Avoid surrounding it with dense chrome in v1.

### 2. Module Boundaries

Organize the frontend into a few clear pieces:

- `map-api`
  - fetches `/api/map/stations`
  - validates response shape
  - maps raw response into frontend-friendly types
- `map-page`
  - owns page-level loading, error, and retry behavior
- `map-view`
  - creates the MapLibre map instance
  - applies camera defaults, bounds, and controls
- `station-layer`
  - converts station data into a single GeoJSON source
  - renders markers as a circle layer
- `map-overlays`
  - renders title, loading state, fetch errors, and generated-at metadata

Keep network concerns out of the map rendering code. The map view should receive already-normalized frontend data.

### 3. Frontend Data Types

Use frontend types that mirror the backend closely:

```ts
type MapStation = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  modes: Array<"tube" | "dlr" | "overground" | "elizabeth-line">;
};

type MapCamera = {
  center: { lat: number; lon: number };
  zoom: number;
  maxBounds: {
    southWest: { lat: number; lon: number };
    northEast: { lat: number; lon: number };
  };
};
```

Flatten `location.lat` and `location.lon` into `lat` and `lon` in the frontend mapper so rendering code stays simple.

## Data Fetching Plan

### Request Strategy

- Fetch `/api/map/stations` once when the map page mounts.
- Do not call TfL directly from the frontend.
- Treat the backend as the source of truth for station scope, deduplication, and bounds.
- Do not poll in v1. A manual page refresh is enough because the dataset is slow-moving.

### State Model

The page should explicitly model:

- `loading`
- `ready`
- `error`

Suggested behavior:

- `loading`: show map shell with a lightweight loading overlay
- `ready`: render the map and station layer
- `error` after `503` or network failure: keep a non-interactive fallback shell with retry action and short explanation

### Validation and Fault Tolerance

- Validate that `version === "v1"` before rendering.
- Validate that `camera`, `maxBounds`, and `stations` exist and are structurally usable.
- If payload validation fails, treat it as a frontend error instead of rendering partial data.
- Keep the UI copy backend-oriented: "Map data is temporarily unavailable."

## Map Rendering Plan

### Rendering Stack

- Use MapLibre GL JS.
- Use a light, low-noise basemap.
- Disable rotation for v1.
- Enable standard drag pan, pinch zoom, double-click zoom, and visible zoom controls.

### Initial Camera

Use backend values exactly on first load:

- `camera.center`
- `camera.zoom`
- `camera.maxBounds`

Do not calculate initial fit-to-bounds in the frontend. The backend contract already defines the intended framing.

### Station Layer

Render stations through one GeoJSON source and one circle layer:

- source data: all stations from `/api/map/stations`
- layer type: `circle`
- circle radius: small but tappable
- circle color: a single high-contrast neutral or brand accent
- circle stroke: thin contrasting outline for visibility on mixed basemap tones

Avoid DOM markers. The station count is large enough that a vector layer is the safer default.

### Marker Interaction

V1 should prepare for interaction without requiring rich behavior yet:

- cursor change on hover is optional
- click handling should exist structurally, even if it only stores a selected station in local state for now
- no popup or side panel is required in v1

This keeps the layer ready for the next step without forcing unfinished station-detail UX into the first release.

## Visual Design Direction

### Overall Feel

The app goal says the product should feel visually striking. For this map, that should come from composition and restraint rather than dense decoration:

- large map-first layout
- crisp overlay typography
- very limited color palette
- a basemap quiet enough to let station density become the visual texture

### Overlay UI

Keep overlays compact:

- top-left title block: product name and short caption
- top-right or bottom-right metadata chip: "Updated from backend data" with formatted `generatedAt`
- error and loading states as floating panels rather than full document replacements

### Marker Style

Use one consistent station marker style in v1:

- small filled dot
- thin outline
- no per-mode color encoding yet

Uniform markers match the backend's station-level normalization and avoid implying mode-specific interaction the UI does not yet support.

## Responsive Plan

### Desktop

- Map should occupy most of the viewport height immediately.
- Navigation controls should sit in a standard corner with enough spacing from overlay cards.
- Overlay panels should avoid covering central London, where marker density is highest.

### Mobile

- Map should remain tall enough to feel primary, ideally near full viewport height.
- Controls and overlays should respect safe areas.
- Marker radius should increase slightly for touch.
- Overlay width should stay narrow so panning is not constantly obstructed.

## Accessibility Plan

- Give the map container a clear accessible name.
- Keep zoom controls keyboard reachable.
- Ensure overlay text and marker contrast pass basic accessibility checks.
- Do not rely on color alone to communicate station presence.
- If keyboard map navigation remains limited, expose that as a known v1 limitation rather than implying full support.

## Error, Empty, and Loading States

### Loading

- Show the base page frame immediately.
- Show a compact loading message over the map region.
- Avoid skeleton markers; the dataset is all-or-nothing.

### Error

Handle two broad cases the same way visually:

- backend returns `503`
- network request fails or times out

Recommended copy:

- title: "Map unavailable"
- body: "Station data could not be loaded right now."
- action: `Retry`

### Empty

The backend should not return an empty successful dataset in normal operation. If it does, treat it as an error state rather than rendering an empty London map.

## Performance Plan

- Build GeoJSON once per successful fetch.
- Add the source and layer once per map instance.
- Update the source only if the dataset changes.
- Avoid rendering React component trees per station.
- Keep overlay rerenders separate from map instance churn.

The backend already sorts and normalizes stations, so the frontend should avoid repeating expensive dataset work.

## Implementation Sequence

1. Create the map page shell and loading or error state container.
2. Add the API client for `/api/map/stations` with response validation and type mapping.
3. Integrate MapLibre with backend camera center, zoom, and max bounds.
4. Add the GeoJSON station source and circle layer.
5. Add visible zoom controls and disable rotation.
6. Add overlay metadata showing formatted `generatedAt`.
7. Add responsive spacing and mobile-safe control placement.
8. Add basic click plumbing for future station selection without exposing a full detail UI yet.

## Acceptance Criteria

- The frontend uses only `GET /api/map/stations` for map data.
- On successful load, the map opens at the backend-provided city-centre camera and respects backend-provided max bounds.
- Every station in the response is rendered as a visible point.
- The map supports drag pan and zoom on desktop and mobile.
- Rotation is disabled and the map remains north-up.
- The page handles backend unavailability with a clear retryable error state.
- The design leaves room for later selected-station and route-overlay features without requiring a rewrite of the map surface.

## Deferred Until Later

- station detail panel or popup
- mode or line filtering
- mode-specific marker styling
- live arrivals
- line or route overlays
- search
- client-side caching beyond normal browser HTTP caching

## Source References

- [docs/map-design.md](/Users/shaynaarora/sandbox/tube/docs/map-design.md)
- [plans/map/backend-design.md](/Users/shaynaarora/sandbox/tube/plans/map/backend-design.md)
- [backend/src/routes/router.py](/Users/shaynaarora/sandbox/tube/backend/src/routes/router.py)
- [backend/src/controllers/map_controller.py](/Users/shaynaarora/sandbox/tube/backend/src/controllers/map_controller.py)
- [backend/src/services/map_service.py](/Users/shaynaarora/sandbox/tube/backend/src/services/map_service.py)
- [backend/src/models/station_dataset.py](/Users/shaynaarora/sandbox/tube/backend/src/models/station_dataset.py)
- [backend/src/models/map_station.py](/Users/shaynaarora/sandbox/tube/backend/src/models/map_station.py)
