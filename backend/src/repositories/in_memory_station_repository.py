from __future__ import annotations

import threading

from backend.src.models.station_dataset import StationDataset


class InMemoryStationRepository:
    def __init__(self) -> None:
        self._dataset: StationDataset | None = None
        self._lock = threading.RLock()

    def get(self) -> StationDataset | None:
        with self._lock:
            return self._dataset

    def save(self, dataset: StationDataset) -> None:
        with self._lock:
            self._dataset = dataset
