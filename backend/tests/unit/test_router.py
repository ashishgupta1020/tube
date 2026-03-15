import unittest

from backend.src.routes.http_response import HttpResponse
from backend.src.routes.router import Router


class FakeMapController:
    def get_map_stations(self) -> HttpResponse:
        return HttpResponse(200, {"Content-Type": "application/json; charset=utf-8"}, {"ok": True})

    def get_health(self) -> HttpResponse:
        return HttpResponse(200, {"Content-Type": "application/json; charset=utf-8"}, {"status": "ok"})


class FakeFrontendController:
    def get_index(self) -> HttpResponse:
        return HttpResponse(200, {"Content-Type": "text/html; charset=utf-8"}, b"index")

    def get_asset(self, path: str) -> HttpResponse:
        return HttpResponse(200, {"Content-Type": "text/plain; charset=utf-8"}, path.encode("utf-8"))


class RouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(FakeMapController(), FakeFrontendController())

    def test_dispatches_frontend_index(self) -> None:
        response = self.router.dispatch("GET", "/")

        self.assertEqual(200, response.status_code)
        self.assertEqual("text/html; charset=utf-8", response.headers["Content-Type"])
        self.assertEqual(b"index", response.body)

    def test_dispatches_frontend_assets(self) -> None:
        response = self.router.dispatch("GET", "/app.js")

        self.assertEqual(200, response.status_code)
        self.assertEqual("text/plain; charset=utf-8", response.headers["Content-Type"])
        self.assertEqual(b"/app.js", response.body)

    def test_returns_not_found_for_non_get_methods(self) -> None:
        response = self.router.dispatch("POST", "/api/map/stations")

        self.assertEqual(404, response.status_code)
        self.assertEqual({"error": "not found"}, response.body)


if __name__ == "__main__":
    unittest.main()
