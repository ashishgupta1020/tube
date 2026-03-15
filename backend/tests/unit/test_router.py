import unittest

from backend.src.routes.router import Router


class FakeMapController:
    def get_map_stations(self) -> tuple[int, dict[str, str], dict]:
        return 200, {"Content-Type": "application/json; charset=utf-8"}, {"ok": True}

    def get_health(self) -> tuple[int, dict[str, str], dict]:
        return 200, {"Content-Type": "application/json; charset=utf-8"}, {"status": "ok"}


class FakeFrontendController:
    def get_index(self) -> tuple[int, dict[str, str], bytes]:
        return 200, {"Content-Type": "text/html; charset=utf-8"}, b"index"

    def get_asset(self, path: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"Content-Type": "text/plain; charset=utf-8"}, path.encode("utf-8")


class RouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(FakeMapController(), FakeFrontendController())

    def test_dispatches_frontend_index(self) -> None:
        status, headers, body = self.router.dispatch("GET", "/")

        self.assertEqual(200, status)
        self.assertEqual("text/html; charset=utf-8", headers["Content-Type"])
        self.assertEqual(b"index", body)

    def test_dispatches_frontend_assets(self) -> None:
        status, headers, body = self.router.dispatch("GET", "/app.js")

        self.assertEqual(200, status)
        self.assertEqual("text/plain; charset=utf-8", headers["Content-Type"])
        self.assertEqual(b"/app.js", body)


if __name__ == "__main__":
    unittest.main()
