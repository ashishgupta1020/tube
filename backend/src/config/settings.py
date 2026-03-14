from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    tfl_base_url: str = "https://api.tfl.gov.uk"
    tfl_app_key: str | None = None
    tfl_timeout_seconds: int = 5
    tfl_retry_count: int = 2
    station_dataset_ttl_seconds: int = 24 * 60 * 60
    stale_data_tolerance_seconds: int = 7 * 24 * 60 * 60
    refresh_check_interval_seconds: int = 300
    response_cache_control: str = "public, max-age=300, stale-while-revalidate=60"
    city_center_lat: float = 51.5074
    city_center_lon: float = -0.1278
    city_center_zoom: float = 10.0
    bounds_padding_ratio: float = 0.08
    min_bounds_padding_degrees: float = 0.02
    scoped_modes: tuple[str, ...] = ("tube", "dlr", "overground", "elizabeth-line")

    @property
    def scoped_modes_query(self) -> str:
        return ",".join(self.scoped_modes)


def load_settings() -> Settings:
    return Settings(
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        tfl_base_url=os.getenv("TFL_BASE_URL", "https://api.tfl.gov.uk"),
        tfl_app_key=os.getenv("TFL_APP_KEY") or None,
        tfl_timeout_seconds=int(os.getenv("TFL_TIMEOUT_SECONDS", "5")),
        tfl_retry_count=int(os.getenv("TFL_RETRY_COUNT", "2")),
        station_dataset_ttl_seconds=int(os.getenv("STATION_DATASET_TTL_SECONDS", str(24 * 60 * 60))),
        stale_data_tolerance_seconds=int(os.getenv("STALE_DATA_TOLERANCE_SECONDS", str(7 * 24 * 60 * 60))),
        refresh_check_interval_seconds=int(os.getenv("REFRESH_CHECK_INTERVAL_SECONDS", "300")),
        response_cache_control=os.getenv(
            "RESPONSE_CACHE_CONTROL",
            "public, max-age=300, stale-while-revalidate=60",
        ),
        city_center_lat=float(os.getenv("CITY_CENTER_LAT", "51.5074")),
        city_center_lon=float(os.getenv("CITY_CENTER_LON", "-0.1278")),
        city_center_zoom=float(os.getenv("CITY_CENTER_ZOOM", "10.0")),
        bounds_padding_ratio=float(os.getenv("BOUNDS_PADDING_RATIO", "0.08")),
        min_bounds_padding_degrees=float(os.getenv("MIN_BOUNDS_PADDING_DEGREES", "0.02")),
    )
