# TfL London Rail API Inventory

## Overview

London Underground data is exposed through TfL's broader Unified API rather than a separate Tube-only API. For this project, the practical base host is `https://api.tfl.gov.uk`, and this document covers the TfL rail services we care about in and around London:

- London Underground with mode `tube`
- DLR with mode and line ID `dlr`
- London Overground with mode `overground`
- Elizabeth line with mode `elizabeth-line` and line ID `elizabeth`

This means the file is no longer Underground-only. It covers the rail services above and excludes unrelated TfL surface transport datasets.

The most relevant API families for this rail product are:

- `Line` for line metadata, service status, and route sequencing
- `StopPoint` for stations, station search, arrivals, and station-serving lines
- `Journey` for trip planning between locations or stations
- `Search` as a fallback when station-specific search is not enough

## Access and Constraints

- Register an application in the TfL API portal and send an `app_key` with requests. TfL's portal notes that `app_id` is no longer required, but some older examples and client snippets may still mention it.
- TfL's current developer guidance allows up to 500 requests per minute and 30,000 requests per day by default. Re-check the portal before production use because quotas and terms can change.
- Rail data is operational and near-real-time. Status, arrivals, and routing responses can lag, fluctuate, or temporarily disagree with one another during incidents or service changes.
- Expect to filter and normalize responses in the application layer. TfL endpoints often return data for multiple modes or include generic transport concepts that are broader than this app's Tube, DLR, Elizabeth line, and Overground scope.
- Overground requires one extra normalization step: the `overground` mode returns individual line IDs under that mode, so application logic should not assume the mode name and line ID are always identical.

## Core APIs We Can Use

### Line

`Line` endpoints are the primary source for service status, route structure, and line metadata.

#### `GET /Line/Mode/tube,dlr,overground,elizabeth-line`

- Returns the line objects for the supported rail modes in one request.
- Use it to bootstrap the list of Underground, DLR, Overground, and Elizabeth line services plus their TfL line IDs.
- Key identifiers: mode list `tube,dlr,overground,elizabeth-line`, line `id`, line `name`, `modeName`.
- Implementation note: Overground entries are returned as individual lines within the `overground` mode rather than a single line ID named `overground`.

#### `GET /Line/Mode/tube,dlr,overground,elizabeth-line/Status`

- Returns current status for all supported rail services in one request.
- Use it for the app's main system-status view or periodic refresh of disruption state across Tube, DLR, Overground, and Elizabeth line.
- Key identifiers: combined `modes`; response includes per-line status and disruption details.

#### `GET /Line/{ids}/Status`

- Returns status for one or more specific lines.
- Use it when the UI is scoped to selected lines and does not need the full system-wide status payload.
- Key identifiers: `ids` is a comma-separated list such as `victoria,dlr,elizabeth` or specific Overground line IDs discovered from `/Line/Mode/tube,dlr,overground,elizabeth-line`.

#### `GET /Line/{ids}/Route/Sequence/{direction}`

- Returns the ordered stop sequence for one or more lines in a given direction.
- Use it for route visualization, line topology, and ordered station lists across all supported rail services.
- Key identifiers: `ids`, `direction` (for example `inbound`, `outbound`, or `all` depending on the line shape).

#### `GET /Line/{id}/Route`

- Returns route information for a specific line.
- Use it when the app needs route context without the full per-direction stop sequence.
- Key identifiers: line `id`.

#### `GET /Line/{id}/Arrivals/{stopPointId}`

- Returns arrival predictions for a line at a specific stop point.
- Use it when the user is already in a line-scoped view and drills into a station/platform combination for Tube, DLR, Elizabeth line, or a specific Overground line.
- Key identifiers: line `id`, station or platform `stopPointId`.

### StopPoint

`StopPoint` endpoints are the main source for station discovery, station detail, and live arrivals.

#### `GET /StopPoint/Mode/tube,dlr,overground,elizabeth-line`

- Returns stop points for the supported rail services.
- Use it for broad station discovery or cached reference data, not for user-typed autocomplete on every keystroke.
- Key identifiers: `modes=tube,dlr,overground,elizabeth-line`; response objects include `id`, `commonName`, `modes`, and location data.

#### `GET /StopPoint/Search/{query}`

- Returns stop point matches for a search query.
- Use it as the primary station autocomplete endpoint because it is stop-point-aware and can be constrained to the supported rail modes.
- Key identifiers: path `query`, optional filters such as `modes=tube,dlr,overground,elizabeth-line`.

#### `GET /StopPoint/{ids}`

- Returns detailed metadata for one or more stop points.
- Use it for station detail pages, resolving station IDs selected from search, and loading station metadata before other calls.
- Key identifiers: one or more `ids`.

#### `GET /StopPoint/{ids}/Arrivals`

- Returns arrival predictions for one or more stop points.
- Use it for live station boards and "next train" views.
- Key identifiers: station or platform `ids`; response often contains line, destination, platform, and expected arrival fields.

#### `GET /StopPoint/{id}/Route`

- Returns route data for a stop point, including lines serving that stop.
- Use it to show which rail services serve a station and to connect station views to route views.
- Key identifiers: stop point `id`.

### Journey

`Journey` endpoints handle trip planning between locations, stations, or coordinates.

#### `GET /Journey/JourneyResults/{from}/to/{to}`

- Returns journey options between origin and destination points.
- Use it for point-to-point trip planning once the user has chosen an origin and destination.
- Key identifiers: `from`, `to`, plus journey-planner query parameters for transport-mode filtering and preference control.
- Implementation note: the endpoint is multimodal by default, so the app should constrain or post-filter results to Tube, DLR, Overground, and Elizabeth line journeys only.

### Search

`Search` is broader than `StopPoint/Search` and should be treated as a fallback rather than the default station search API.

#### `GET /Search/{query}`

- Returns matches across TfL entities, not just stations.
- Use it only if `StopPoint/Search` fails to satisfy a product need such as broader entity search or mixed-result lookup.
- Key identifiers: path `query`; results may need additional filtering to avoid non-rail entities.

## Recommended Usage In This App

- Line status: use `GET /Line/Mode/tube,dlr,overground,elizabeth-line/Status` for the default overview and `GET /Line/{ids}/Status` for scoped refreshes.
- Station autocomplete: use `GET /StopPoint/Search/{query}` with `modes=tube,dlr,overground,elizabeth-line`.
- Station detail: resolve the chosen station with `GET /StopPoint/{ids}` and enrich it with `GET /StopPoint/{id}/Route` if line-serving data is needed.
- Live arrivals: use `GET /StopPoint/{ids}/Arrivals` for station boards; use `GET /Line/{id}/Arrivals/{stopPointId}` only when the workflow is already line-scoped.
- Route visualization and ordered stops: use `GET /Line/{ids}/Route/Sequence/{direction}` as the main topology source and `GET /StopPoint/{id}/Route` for station-centric route context.
- Trip planning: use `GET /Journey/JourneyResults/{from}/to/{to}` and explicitly constrain or filter to Tube, DLR, Overground, and Elizabeth line journeys.
- Line identity handling: treat Elizabeth line as line ID `elizabeth`, and do not assume Overground has a single line ID matching its mode name.

## Explicit Exclusions

This file intentionally excludes non-rail or out-of-scope areas of the TfL platform, including:

- bus APIs
- Santander Cycles and bike point APIs
- roads, traffic, and river services
- air quality, crowding, and other peripheral datasets unless they become a direct rail feature requirement
- broader National Rail coverage outside Elizabeth line and London Overground
- tram and other non-target TfL rail modes unless the product scope expands

## Sources

- TfL Unified API docs: <https://api.tfl.gov.uk>
- TfL Swagger definition: <https://api.tfl.gov.uk/swagger/docs/v1>
- TfL developer portal and product signup: <https://api-portal.tfl.gov.uk>
- TfL open data / API terms guidance: <https://tfl.gov.uk/info-for/open-data-users/>
