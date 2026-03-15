import unittest
from dataclasses import replace
from datetime import timedelta

from backend.src.config.settings import Settings
from backend.src.integrations.tfl.client import TflClientError
from backend.src.models.station_dataset import utc_now
from backend.src.normalizers.station_normalizer import StationNormalizer
from backend.src.repositories.in_memory_station_repository import InMemoryStationRepository
from backend.src.services.map_service import MapService, ServiceUnavailableError


class FakeTflClient:
    def __init__(self, stop_points: list[dict]) -> None:
        self.stop_points = stop_points
        self.raise_error = False

    def fetch_stop_points(self) -> list[dict]:
        if self.raise_error:
            raise TflClientError("upstream failed")
        return self.stop_points


class MapServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            station_dataset_ttl_seconds=60,
            stale_data_tolerance_seconds=3600,
        )
        self.stop_points = [
            {
                "id": "940GZZDLBNK",
                "stationNaptan": "940GZZDLBNK",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank DLR Station",
                "lat": 51.5133,
                "lon": -0.0886,
                "modes": ["dlr"],
                "stopType": "NaptanMetroStation",
            },
            {
                "id": "940GZZLUBNK",
                "stationNaptan": "940GZZLUBNK",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank Underground Station",
                "lat": 51.5134,
                "lon": -0.0887,
                "modes": ["tube"],
                "stopType": "NaptanMetroStation",
            },
        ]

    def test_initial_request_fetches_and_returns_dataset(self) -> None:
        service = MapService(
            settings=self.settings,
            tfl_client=FakeTflClient(self.stop_points),
            station_normalizer=StationNormalizer(self.settings.scoped_modes),
            station_repository=InMemoryStationRepository(),
        )

        dataset = service.get_map_stations_dataset()
        response = dataset.to_response_dict()

        self.assertEqual("v1", dataset.version)
        self.assertEqual("v1", response["version"])
        self.assertEqual(1, len(response["stations"]))
        self.assertEqual("HUBBAN", response["stations"][0]["id"])
        self.assertEqual(["dlr", "tube"], response["stations"][0]["modes"])

    def test_expired_dataset_falls_back_to_stale_copy_when_refresh_fails(self) -> None:
        client = FakeTflClient(self.stop_points)
        repository = InMemoryStationRepository()
        service = MapService(
            settings=self.settings,
            tfl_client=client,
            station_normalizer=StationNormalizer(self.settings.scoped_modes),
            station_repository=repository,
        )

        service.get_map_stations_dataset()
        dataset = repository.get()
        assert dataset is not None
        expired_dataset = replace(
            dataset,
            expires_at=utc_now() - timedelta(seconds=1),
            updated_at=utc_now() - timedelta(seconds=10),
        )
        repository.save(expired_dataset)
        client.raise_error = True

        response = service.get_map_stations_dataset().to_response_dict()

        self.assertEqual(1, len(response["stations"]))

    def test_expired_dataset_raises_when_stale_copy_is_too_old(self) -> None:
        client = FakeTflClient(self.stop_points)
        repository = InMemoryStationRepository()
        service = MapService(
            settings=self.settings,
            tfl_client=client,
            station_normalizer=StationNormalizer(self.settings.scoped_modes),
            station_repository=repository,
        )

        service.get_map_stations_dataset()
        dataset = repository.get()
        assert dataset is not None
        expired_dataset = replace(
            dataset,
            expires_at=utc_now() - timedelta(seconds=1),
            updated_at=utc_now() - timedelta(seconds=self.settings.stale_data_tolerance_seconds + 1),
        )
        repository.save(expired_dataset)
        client.raise_error = True

        with self.assertRaises(ServiceUnavailableError):
            service.get_map_stations_dataset()

    def test_background_refresh_keeps_stale_dataset_without_raising(self) -> None:
        client = FakeTflClient(self.stop_points)
        repository = InMemoryStationRepository()
        service = MapService(
            settings=self.settings,
            tfl_client=client,
            station_normalizer=StationNormalizer(self.settings.scoped_modes),
            station_repository=repository,
        )

        service.get_map_stations_dataset()
        dataset = repository.get()
        assert dataset is not None
        expired_dataset = replace(
            dataset,
            expires_at=utc_now() - timedelta(seconds=1),
            updated_at=utc_now() - timedelta(seconds=10),
        )
        repository.save(expired_dataset)
        client.raise_error = True

        service.refresh_if_due()

        cached_dataset = repository.get()
        self.assertIsNotNone(cached_dataset)
        self.assertEqual(expired_dataset, cached_dataset)


if __name__ == "__main__":
    unittest.main()
