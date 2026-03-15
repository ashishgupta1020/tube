from __future__ import annotations

from collections.abc import Callable

from backend.src.controllers.frontend_controller import FrontendController
from backend.src.controllers.map_controller import MapController
from backend.src.routes.http_response import HttpResponse, not_found_response


class Router:
    def __init__(self, map_controller: MapController, frontend_controller: FrontendController) -> None:
        self._map_controller = map_controller
        self._frontend_controller = frontend_controller
        self._get_routes: dict[str, Callable[[], HttpResponse]] = {
            "/api/map/stations": self._map_controller.get_map_stations,
            "/health": self._map_controller.get_health,
            "/": self._frontend_controller.get_index,
            "/index.html": self._frontend_controller.get_index,
        }

    def dispatch(self, method: str, path: str) -> HttpResponse:
        if method != "GET":
            return not_found_response()

        handler = self._get_routes.get(path)
        if handler is not None:
            return handler()

        return self._frontend_controller.get_asset(path)
