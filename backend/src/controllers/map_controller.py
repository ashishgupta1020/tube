from backend.src.config.settings import Settings
from backend.src.services.map_service import MapService, ServiceUnavailableError


class MapController:
    def __init__(self, map_service: MapService, settings: Settings) -> None:
        self._map_service = map_service
        self._settings = settings

    def get_map_stations(self) -> tuple[int, dict[str, str], dict]:
        try:
            payload = self._map_service.get_map_stations_response()
            return (
                200,
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Cache-Control": self._settings.response_cache_control,
                },
                payload,
            )
        except ServiceUnavailableError as exc:
            return (
                503,
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Cache-Control": "no-store",
                },
                {"error": str(exc)},
            )

    def get_health(self) -> tuple[int, dict[str, str], dict]:
        return (
            200,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store",
            },
            {"status": "ok"},
        )
