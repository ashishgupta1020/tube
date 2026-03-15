from __future__ import annotations

import logging
import threading
from datetime import timedelta

from backend.src.config.settings import Settings
from backend.src.integrations.tfl.client import TflClient, TflClientError
from backend.src.models.map_station import MapStation
from backend.src.models.station_dataset import StationDataset, utc_now
from backend.src.normalizers.station_normalizer import StationNormalizer
from backend.src.repositories.in_memory_station_repository import InMemoryStationRepository
from backend.src.utils.bounds import compute_padded_bounds


LOGGER = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    """Raised when the backend cannot serve a usable map dataset."""


class MapService:
    def __init__(
        self,
        settings: Settings,
        tfl_client: TflClient,
        station_normalizer: StationNormalizer,
        station_repository: InMemoryStationRepository,
    ) -> None:
        self._settings = settings
        self._tfl_client = tfl_client
        self._station_normalizer = station_normalizer
        self._station_repository = station_repository
        self._refresh_lock = threading.Lock()

    def get_map_stations_dataset(self) -> StationDataset:
        """Return the current map dataset, refreshing it when required."""

        dataset = self._station_repository.get()
        if self._is_fresh(dataset):
            return dataset

        return self._refresh_or_serve_stale(dataset)

    def refresh_if_due(self) -> None:
        """Refresh the cached dataset when no fresh copy is currently available."""

        dataset = self._station_repository.get()
        if self._is_fresh(dataset):
            return

        try:
            self._refresh_dataset()
        except ServiceUnavailableError as exc:
            if self._can_serve_stale(dataset):
                LOGGER.info("background refresh failed; keeping stale station dataset available: %s", exc)
                return
            raise

    def _refresh_or_serve_stale(self, dataset: StationDataset | None) -> StationDataset:
        """Refresh the dataset or fall back to a stale but still usable copy."""

        try:
            return self._refresh_dataset()
        except ServiceUnavailableError as exc:
            if self._can_serve_stale(dataset):
                assert dataset is not None
                LOGGER.warning("serving stale station dataset after refresh failure: %s", exc)
                return dataset
            raise ServiceUnavailableError("station dataset is unavailable") from exc

    def _refresh_dataset(self) -> StationDataset:
        """Build and store a fresh dataset if one is not already cached."""

        with self._refresh_lock:
            existing_dataset = self._station_repository.get()
            if self._is_fresh(existing_dataset):
                return existing_dataset

            stations = self._fetch_stations()
            self._validate_station_count(stations, existing_dataset)
            dataset = self._build_dataset(stations)
            self._station_repository.save(dataset)

            LOGGER.info(
                "refreshed station dataset station_count=%s expires_at=%s",
                len(stations),
                dataset.expires_at.isoformat(),
            )
            return dataset

    def _fetch_stations(self) -> tuple[MapStation, ...]:
        """Fetch and normalize the upstream TfL stop points."""

        try:
            stop_points = self._tfl_client.fetch_stop_points()
        except TflClientError as exc:
            raise ServiceUnavailableError("failed to refresh station dataset") from exc

        stations = self._station_normalizer.normalize(stop_points)
        if not stations:
            raise ServiceUnavailableError("normalization produced no stations")
        return stations

    def _validate_station_count(
        self,
        stations: tuple[MapStation, ...],
        existing_dataset: StationDataset | None,
    ) -> None:
        """Reject implausibly small refreshes when a previous dataset exists."""

        if existing_dataset is None:
            return

        minimum_station_count = int(len(existing_dataset.stations) * 0.75)
        if len(stations) < minimum_station_count:
            raise ServiceUnavailableError("refreshed station dataset was unexpectedly small")

    def _build_dataset(self, stations: tuple[MapStation, ...]) -> StationDataset:
        """Construct the frontend-facing dataset model from normalized stations."""

        south_west, north_east = compute_padded_bounds(
            stations,
            padding_ratio=self._settings.bounds_padding_ratio,
            min_padding_degrees=self._settings.min_bounds_padding_degrees,
        )

        now = utc_now()
        return StationDataset(
            version="v1",
            generated_at=now,
            updated_at=now,
            expires_at=now + timedelta(seconds=self._settings.station_dataset_ttl_seconds),
            camera_center_lat=self._settings.city_center_lat,
            camera_center_lon=self._settings.city_center_lon,
            camera_zoom=self._settings.city_center_zoom,
            south_west_lat=south_west["lat"],
            south_west_lon=south_west["lon"],
            north_east_lat=north_east["lat"],
            north_east_lon=north_east["lon"],
            stations=stations,
        )

    def _is_fresh(self, dataset: StationDataset | None) -> bool:
        """Return whether the dataset exists and is still within its TTL."""

        return dataset is not None and not dataset.is_expired()

    def _can_serve_stale(self, dataset: StationDataset | None) -> bool:
        """Return whether the dataset is stale but still within the allowed tolerance."""

        return dataset is not None and dataset.is_usable_stale(self._settings.stale_data_tolerance_seconds)
