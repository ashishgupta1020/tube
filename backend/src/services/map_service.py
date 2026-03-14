import logging
import threading
from datetime import timedelta

from backend.src.config.settings import Settings
from backend.src.integrations.tfl.client import TflClient, TflClientError
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

    def get_map_stations_response(self) -> dict:
        dataset = self._get_or_refresh_dataset()
        return dataset.to_response_dict()

    def refresh_if_due(self) -> None:
        dataset = self._station_repository.get()
        if dataset is None or dataset.is_expired():
            try:
                self._refresh_dataset()
            except ServiceUnavailableError:
                if dataset is not None and dataset.is_usable_stale(self._settings.stale_data_tolerance_seconds):
                    LOGGER.info("background refresh failed; keeping stale station dataset available")
                    return
                raise

    def _get_or_refresh_dataset(self) -> StationDataset:
        dataset = self._station_repository.get()
        if dataset is None:
            return self._refresh_dataset()

        if not dataset.is_expired():
            return dataset

        try:
            return self._refresh_dataset()
        except Exception as exc:
            if dataset.is_usable_stale(self._settings.stale_data_tolerance_seconds):
                LOGGER.warning("serving stale station dataset after refresh failure: %s", exc)
                return dataset
            raise ServiceUnavailableError("station dataset is unavailable") from exc

    def _refresh_dataset(self) -> StationDataset:
        with self._refresh_lock:
            existing_dataset = self._station_repository.get()
            if existing_dataset is not None and not existing_dataset.is_expired():
                return existing_dataset

            try:
                stop_points = self._tfl_client.fetch_stop_points()
                stations = self._station_normalizer.normalize(stop_points)
            except TflClientError as exc:
                raise ServiceUnavailableError("failed to refresh station dataset") from exc

            if not stations:
                raise ServiceUnavailableError("normalization produced no stations")

            if existing_dataset is not None:
                minimum_station_count = int(len(existing_dataset.stations) * 0.75)
                if len(stations) < minimum_station_count:
                    raise ServiceUnavailableError("refreshed station dataset was unexpectedly small")

            south_west, north_east = compute_padded_bounds(
                stations,
                padding_ratio=self._settings.bounds_padding_ratio,
                min_padding_degrees=self._settings.min_bounds_padding_degrees,
            )

            now = utc_now()
            dataset = StationDataset(
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
            self._station_repository.save(dataset)

            LOGGER.info(
                "refreshed station dataset station_count=%s expires_at=%s",
                len(stations),
                dataset.expires_at.isoformat(),
            )
            return dataset
