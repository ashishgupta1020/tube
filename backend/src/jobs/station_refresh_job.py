import logging
import threading

from backend.src.config.settings import Settings
from backend.src.services.map_service import MapService


LOGGER = logging.getLogger(__name__)


class StationRefreshJob:
    def __init__(self, map_service: MapService, settings: Settings) -> None:
        self._map_service = map_service
        self._settings = settings
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="station-refresh-job",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1)

    def _run(self) -> None:
        self._refresh_if_due()
        while not self._stop_event.wait(self._settings.refresh_check_interval_seconds):
            self._refresh_if_due()

    def _refresh_if_due(self) -> None:
        try:
            self._map_service.refresh_if_due()
        except Exception as exc:
            LOGGER.warning("background station refresh failed: %s", exc)
