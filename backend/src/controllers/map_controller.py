from backend.src.config.settings import Settings
from backend.src.routes.http_response import HttpResponse, json_response, service_unavailable_response
from backend.src.services.map_service import MapService, ServiceUnavailableError


class MapController:
    def __init__(self, map_service: MapService, settings: Settings) -> None:
        self._map_service = map_service
        self._settings = settings

    def get_map_stations(self) -> HttpResponse:
        try:
            return json_response(
                200,
                self._map_service.get_map_stations_dataset().to_response_dict(),
                cache_control=self._settings.response_cache_control,
            )
        except ServiceUnavailableError as exc:
            return service_unavailable_response(str(exc))

    def get_health(self) -> HttpResponse:
        return json_response(200, {"status": "ok"})
