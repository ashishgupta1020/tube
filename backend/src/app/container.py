from __future__ import annotations

from dataclasses import dataclass

from backend.src.config.settings import Settings, load_settings
from backend.src.controllers.map_controller import MapController
from backend.src.integrations.tfl.client import TflClient
from backend.src.jobs.station_refresh_job import StationRefreshJob
from backend.src.normalizers.station_normalizer import StationNormalizer
from backend.src.repositories.in_memory_station_repository import InMemoryStationRepository
from backend.src.routes.router import Router
from backend.src.services.map_service import MapService


@dataclass
class AppContainer:
    settings: Settings
    map_service: MapService
    map_controller: MapController
    router: Router
    refresh_job: StationRefreshJob


def build_container(settings: Settings | None = None) -> AppContainer:
    config = settings or load_settings()
    repository = InMemoryStationRepository()
    tfl_client = TflClient(config)
    normalizer = StationNormalizer(config.scoped_modes)
    map_service = MapService(
        settings=config,
        tfl_client=tfl_client,
        station_normalizer=normalizer,
        station_repository=repository,
    )
    map_controller = MapController(map_service, config)
    router = Router(map_controller)
    refresh_job = StationRefreshJob(map_service, config)
    return AppContainer(
        settings=config,
        map_service=map_service,
        map_controller=map_controller,
        router=router,
        refresh_job=refresh_job,
    )
