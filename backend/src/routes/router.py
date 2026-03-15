from __future__ import annotations

from backend.src.controllers.frontend_controller import FrontendController
from backend.src.controllers.map_controller import MapController


class Router:
    def __init__(self, map_controller: MapController, frontend_controller: FrontendController) -> None:
        self._map_controller = map_controller
        self._frontend_controller = frontend_controller

    def dispatch(self, method: str, path: str) -> tuple[int, dict[str, str], bytes | dict]:
        if method == "GET" and path == "/api/map/stations":
            return self._map_controller.get_map_stations()
        if method == "GET" and path == "/health":
            return self._map_controller.get_health()
        if method == "GET" and path in {"/", "/index.html"}:
            return self._frontend_controller.get_index()
        if method == "GET":
            return self._frontend_controller.get_asset(path)

        return (
            404,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store",
            },
            {"error": "not found"},
        )
