from backend.src.controllers.map_controller import MapController


class Router:
    def __init__(self, map_controller: MapController) -> None:
        self._map_controller = map_controller

    def dispatch(self, method: str, path: str) -> tuple[int, dict[str, str], dict]:
        if method == "GET" and path == "/api/map/stations":
            return self._map_controller.get_map_stations()
        if method == "GET" and path == "/health":
            return self._map_controller.get_health()

        return (
            404,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store",
            },
            {"error": "not found"},
        )
