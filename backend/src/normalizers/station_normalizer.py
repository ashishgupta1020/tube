from __future__ import annotations

from collections import defaultdict

from backend.src.models.map_station import MapStation


class StationNormalizer:
    _STOP_TYPE_PRIORITY = {
        "TransportInterchange": 100,
        "NaptanMetroStation": 90,
        "NaptanRailStation": 90,
        "NaptanMetroAccessArea": 80,
        "NaptanRailAccessArea": 80,
        "NaptanMetroEntrance": 70,
        "NaptanRailEntrance": 70,
        "NaptanMetroPlatform": 60,
    }

    def __init__(self, scoped_modes: tuple[str, ...]) -> None:
        self._scoped_modes = set(scoped_modes)

    def normalize(self, stop_points: list[dict]) -> tuple[MapStation, ...]:
        grouped_stop_points: dict[str, list[dict]] = defaultdict(list)

        for stop_point in stop_points:
            group_key = self._group_key(stop_point)
            if group_key is None:
                continue
            grouped_stop_points[group_key].append(stop_point)

        normalized_stations: list[MapStation] = []

        for group_key, group in grouped_stop_points.items():
            station = self._normalize_group(group_key, group)
            if station is not None:
                normalized_stations.append(station)

        normalized_stations.sort(key=lambda station: (station.name.casefold(), station.id))
        return tuple(normalized_stations)

    def _normalize_group(self, group_key: str, stop_points: list[dict]) -> MapStation | None:
        scoped_modes = sorted(
            {
                mode
                for stop_point in stop_points
                for mode in stop_point.get("modes", [])
                if mode in self._scoped_modes
            }
        )
        if not scoped_modes:
            return None

        candidate = max(stop_points, key=lambda stop_point: self._candidate_score(group_key, stop_point))
        lat = candidate.get("lat")
        lon = candidate.get("lon")
        common_name = candidate.get("commonName")

        if common_name is None:
            return None
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return None

        canonical_id = candidate.get("hubNaptanCode") or candidate.get("stationNaptan") or candidate.get("id")
        if not canonical_id:
            return None

        return MapStation(
            id=str(canonical_id),
            name=str(common_name),
            lat=float(lat),
            lon=float(lon),
            modes=tuple(scoped_modes),
        )

    def _group_key(self, stop_point: dict) -> str | None:
        hub_naptan_code = stop_point.get("hubNaptanCode")
        if hub_naptan_code:
            return "hub:{code}".format(code=hub_naptan_code)

        station_naptan = stop_point.get("stationNaptan")
        if station_naptan:
            return "station:{code}".format(code=station_naptan)

        stop_point_id = stop_point.get("id")
        if stop_point_id:
            return "id:{code}".format(code=stop_point_id)

        return None

    def _candidate_score(self, group_key: str, stop_point: dict) -> tuple[int, int, int, int]:
        stop_type = stop_point.get("stopType")
        priority = self._STOP_TYPE_PRIORITY.get(stop_type, 0)
        lat = stop_point.get("lat")
        lon = stop_point.get("lon")
        has_coordinates = int(isinstance(lat, (int, float)) and isinstance(lon, (int, float)))
        mode_count = len([mode for mode in stop_point.get("modes", []) if mode in self._scoped_modes])

        key_matches_id = 0
        if group_key.startswith("hub:") and stop_point.get("hubNaptanCode") == group_key.split(":", 1)[1]:
            key_matches_id = 1
        if group_key.startswith("station:") and stop_point.get("stationNaptan") == group_key.split(":", 1)[1]:
            key_matches_id = 1
        if group_key.startswith("id:") and stop_point.get("id") == group_key.split(":", 1)[1]:
            key_matches_id = 1

        return (priority, key_matches_id, has_coordinates, mode_count)
