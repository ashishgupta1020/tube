# London Rail Map Design

## Purpose

This document defines the first map element for the app: a navigable map of London and nearby areas covered by the scoped TfL rail network, with a visible marker for every station in that network.

The feature is intentionally basic for v1. It should establish the map surface, station coverage, and interaction model without yet adding route lines, arrival boards, or journey overlays.

## Product Goal

The map should answer three simple questions immediately:

1. Where does the scoped TfL rail network operate around London?
2. Where is each station located?
3. How can the user move around the map comfortably?

The first release should optimize for orientation and exploration rather than dense operational detail.

## Scoped Network

The map includes only the rail services already scoped in [docs/tfl-tube-api.md](/Users/shaynaarora/sandbox/tube/docs/tfl-tube-api.md):

- London Underground
- DLR
- London Overground
- Elizabeth line

Anything outside that scope is out of view for this map element, including buses, trams, river services, and broader National Rail coverage.

## Core Design Decisions

### 1. Geographic Coverage

- The map should cover Greater London plus the nearby areas reached by the scoped services.
- The initial camera should use a hard-coded city-centre view rather than fitting the full station dataset on first load.
- The default zoom should show central London clearly while still giving enough surrounding context to signal that the network extends beyond the centre.
- The map should apply max bounds slightly larger than the station bounding box so users can pan a little beyond the network without getting lost in irrelevant geography.
- If the station dataset fails to load, keep the same city-centre fallback camera rather than switching to a different regional frame.

### 2. Station Representation

- Show one marker per station, not one marker per platform or child stop point.
- Interchange stations should appear once, even if they serve multiple scoped modes.
- Each marker should be anchored to the station's canonical latitude and longitude from TfL stop point data.
- Marker styling should be minimal and consistent in v1: a small high-contrast dot with a thin outline so it remains visible on light or dark basemap areas.
- Selected and hovered markers can be differentiated later, but the first version only needs a default marker state.

### 3. Basic Navigation

- Users must be able to pan by dragging.
- Users must be able to zoom with on-map controls and standard map gestures.
- Include visible zoom controls on the map at all times so navigation works without relying on trackpad or mouse-wheel familiarity.
- Double-click zoom can remain enabled.
- Scroll-wheel zoom should not aggressively hijack page scrolling; it should either require map focus/hover or follow the map library's standard restrained desktop behavior.

## Map Surface

### Recommended Rendering Stack

- Use MapLibre GL JS for the map surface.
- Use a neutral basemap style that emphasizes land, water, and major roads without overpowering station markers.
- Keep route line overlays out of v1. The base map should communicate place and geography; station markers communicate the network.

MapLibre is a good fit here because it is built for interactive WebGL maps and includes standard map controls such as navigation controls out of the box.

### Visual Style

- Default to a light, low-noise basemap so station markers remain the strongest visual element.
- Avoid heavy POI labeling in the first cut; excessive labels will compete with hundreds of stations.
- Keep markers visually uniform across all scoped modes for v1. Mode-specific coloring can come later if the product adds line filters or route overlays.

## Data Design

### Primary Data Source

- Use `GET /StopPoint/Mode/tube,dlr,overground,elizabeth-line` as the broad station source.
- Normalize the result set to station-level entities before rendering.
- Preserve TfL identifiers so later features can connect markers to station detail, arrivals, and route lookups.

### Station Normalization Rules

- Prefer station or stop-area records over platform-level records.
- Deduplicate stations that appear across multiple scoped modes.
- Store one map entity per station with:
  - TfL station ID
  - station name
  - latitude
  - longitude
  - supported scoped modes
- Exclude malformed records that do not have usable coordinates.

### Initial Data Model

Each rendered station should be representable as:

```ts
type RailStationMapPoint = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  modes: Array<"tube" | "dlr" | "overground" | "elizabeth-line">;
};
```

## Interaction Model

### Default State

- On load, the map opens to the default city-centre camera.
- All station markers render immediately after station data resolves.
- No station is preselected by default.

### Marker Interaction

- V1 requires marker visibility, not rich marker interaction.
- A click target should still be large enough for later expansion into selection or station detail.
- Hover states are optional in the first pass and should not be required for usability.

### Navigation Controls

- Include a visible zoom-in and zoom-out control in a standard map corner.
- Support drag pan on desktop and touch pan on mobile.
- Support pinch zoom on touch devices.
- Keep rotation disabled for v1 so the map remains north-up and easier to scan.

## Responsive Behavior

- On desktop, the map should occupy enough width and height to feel like a primary surface, not a thumbnail.
- On mobile, the map should still allow pan and zoom without accidental control overlap.
- Marker size should remain tappable on touch screens without becoming visually heavy on desktop.
- Control placement should avoid safe-area collisions and remain reachable with one hand on mobile.

## Performance Notes

- The marker count is large enough that rendering should be deliberate, but still manageable for a first release.
- Prefer a single GeoJSON source plus a symbol or circle layer over hundreds of individually mounted DOM markers.
- Compute the initial bounds from data once per load, not on every render.
- Leave clustering out of v1 unless station density proves unreadable in testing. The initial requirement is "every station visible on the map," so clustering would work against that unless carefully designed.

## Accessibility

- The map container should have a clear accessible name.
- Zoom controls must be keyboard reachable.
- The initial experience should not rely on color alone to indicate station presence.
- The map should preserve enough contrast between markers and the basemap.
- If full keyboard map navigation is not implemented in v1, that limitation should be explicit and non-map alternatives should be planned for later.

## Out of Scope For This Element

- line polylines or route overlays
- live arrivals or disruption badges on the map
- journey path rendering
- station detail popovers or side panels
- filtering by line or mode
- clustering, heatmaps, or density views

## Acceptance Criteria

- A user can open the page and immediately see a map covering the scoped London rail network footprint.
- Every scoped station is represented by a visible marker at station level.
- The user can pan and zoom with standard interactions on desktop and mobile.
- The map remains north-up and does not rotate.
- The map design leaves room for later station selection and route overlays without needing to be redesigned from scratch.

## Sources

- TfL rail API inventory for this repo: [docs/tfl-tube-api.md](/Users/shaynaarora/sandbox/tube/docs/tfl-tube-api.md)
- TfL Unified API: <https://api.tfl.gov.uk>
- MapLibre GL JS docs: <https://maplibre.org/maplibre-gl-js/docs/>
- MapLibre `NavigationControl` docs: <https://maplibre.org/maplibre-gl-js/docs/API/classes/NavigationControl/>
