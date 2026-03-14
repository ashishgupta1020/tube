from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.src.models.map_station import MapStation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class StationDataset:
    version: str
    generated_at: datetime
    updated_at: datetime
    expires_at: datetime
    camera_center_lat: float
    camera_center_lon: float
    camera_zoom: float
    south_west_lat: float
    south_west_lon: float
    north_east_lat: float
    north_east_lon: float
    stations: tuple[MapStation, ...]

    def is_expired(self, now: datetime | None = None) -> bool:
        current_time = now or utc_now()
        return current_time >= self.expires_at

    def is_usable_stale(self, stale_tolerance_seconds: int, now: datetime | None = None) -> bool:
        current_time = now or utc_now()
        age_seconds = (current_time - self.updated_at).total_seconds()
        return age_seconds <= stale_tolerance_seconds

    def to_response_dict(self) -> dict:
        return {
            "version": self.version,
            "generatedAt": self.generated_at.isoformat(),
            "camera": {
                "center": {
                    "lat": self.camera_center_lat,
                    "lon": self.camera_center_lon,
                },
                "zoom": self.camera_zoom,
                "maxBounds": {
                    "southWest": {
                        "lat": self.south_west_lat,
                        "lon": self.south_west_lon,
                    },
                    "northEast": {
                        "lat": self.north_east_lat,
                        "lon": self.north_east_lon,
                    },
                },
            },
            "stations": [station.to_dict() for station in self.stations],
        }
