from backend.src.models.map_station import MapStation


def compute_padded_bounds(
    stations: tuple[MapStation, ...],
    padding_ratio: float,
    min_padding_degrees: float,
) -> tuple[dict[str, float], dict[str, float]]:
    if not stations:
        raise ValueError("cannot compute bounds without stations")

    min_lat = min(station.lat for station in stations)
    max_lat = max(station.lat for station in stations)
    min_lon = min(station.lon for station in stations)
    max_lon = max(station.lon for station in stations)

    lat_padding = max((max_lat - min_lat) * padding_ratio, min_padding_degrees)
    lon_padding = max((max_lon - min_lon) * padding_ratio, min_padding_degrees)

    south_west = {
        "lat": min_lat - lat_padding,
        "lon": min_lon - lon_padding,
    }
    north_east = {
        "lat": max_lat + lat_padding,
        "lon": max_lon + lon_padding,
    }
    return south_west, north_east
