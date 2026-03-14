from dataclasses import dataclass


@dataclass(frozen=True)
class MapStation:
    id: str
    name: str
    lat: float
    lon: float
    modes: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "location": {"lat": self.lat, "lon": self.lon},
            "modes": list(self.modes),
        }
