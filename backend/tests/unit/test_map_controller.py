import unittest

from backend.src.config.settings import Settings
from backend.src.controllers.map_controller import MapController
from backend.src.services.map_service import ServiceUnavailableError


class FakeDataset:
    def to_response_dict(self) -> dict:
        return {"version": "v1", "stations": []}


class FakeMapService:
    def __init__(self) -> None:
        self.raise_error = False

    def get_map_stations_dataset(self) -> FakeDataset:
        if self.raise_error:
            raise ServiceUnavailableError("station dataset is unavailable")
        return FakeDataset()


class MapControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakeMapService()
        self.controller = MapController(self.service, Settings())

    def test_get_map_stations_returns_json_response(self) -> None:
        response = self.controller.get_map_stations()

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json; charset=utf-8", response.headers["Content-Type"])
        self.assertEqual({"version": "v1", "stations": []}, response.body)

    def test_get_map_stations_maps_service_unavailable(self) -> None:
        self.service.raise_error = True

        response = self.controller.get_map_stations()

        self.assertEqual(503, response.status_code)
        self.assertEqual({"error": "station dataset is unavailable"}, response.body)


if __name__ == "__main__":
    unittest.main()
