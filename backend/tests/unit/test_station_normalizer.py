import unittest

from backend.src.normalizers.station_normalizer import StationNormalizer
from backend.src.utils.bounds import compute_padded_bounds


class StationNormalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = StationNormalizer(("tube", "dlr", "overground", "elizabeth-line"))

    def test_merges_interchange_station_across_modes(self) -> None:
        stop_points = [
            {
                "id": "HUBBAN",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank",
                "lat": 51.5135,
                "lon": -0.0890,
                "modes": ["bus", "dlr", "tube"],
                "stopType": "TransportInterchange",
            },
            {
                "id": "940GZZDLBNK",
                "stationNaptan": "940GZZDLBNK",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank DLR Station",
                "lat": 51.5133,
                "lon": -0.0886,
                "modes": ["dlr"],
                "stopType": "NaptanMetroStation",
            },
            {
                "id": "940GZZLUBNK",
                "stationNaptan": "940GZZLUBNK",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank Underground Station",
                "lat": 51.5134,
                "lon": -0.0887,
                "modes": ["tube"],
                "stopType": "NaptanMetroStation",
            },
            {
                "id": "9400ZZLUBNK1",
                "stationNaptan": "940GZZLUBNK",
                "hubNaptanCode": "HUBBAN",
                "commonName": "Bank Underground Station",
                "lat": 51.5132,
                "lon": -0.0888,
                "modes": ["tube"],
                "stopType": "NaptanMetroPlatform",
            },
        ]

        stations = self.normalizer.normalize(stop_points)

        self.assertEqual(1, len(stations))
        self.assertEqual("HUBBAN", stations[0].id)
        self.assertEqual("Bank", stations[0].name)
        self.assertEqual(("dlr", "tube"), stations[0].modes)

    def test_prefers_station_level_record_over_platform(self) -> None:
        stop_points = [
            {
                "id": "9400ZZDLABR0",
                "stationNaptan": "940GZZDLABR",
                "commonName": "Abbey Road DLR Station",
                "lat": 51.53209,
                "lon": 0.00383,
                "modes": ["dlr"],
                "stopType": "NaptanMetroEntrance",
            },
            {
                "id": "940GZZDLABR",
                "stationNaptan": "940GZZDLABR",
                "commonName": "Abbey Road DLR Station",
                "lat": 51.531926,
                "lon": 0.003737,
                "modes": ["dlr"],
                "stopType": "NaptanMetroStation",
            },
        ]

        stations = self.normalizer.normalize(stop_points)

        self.assertEqual(1, len(stations))
        self.assertEqual("940GZZDLABR", stations[0].id)
        self.assertAlmostEqual(51.531926, stations[0].lat)

    def test_compute_padded_bounds(self) -> None:
        stations = self.normalizer.normalize(
            [
                {
                    "id": "940GZZDLABR",
                    "stationNaptan": "940GZZDLABR",
                    "commonName": "Abbey Road DLR Station",
                    "lat": 51.531926,
                    "lon": 0.003737,
                    "modes": ["dlr"],
                    "stopType": "NaptanMetroStation",
                },
                {
                    "id": "940GZZLUACT",
                    "stationNaptan": "940GZZLUACT",
                    "commonName": "Acton Town Underground Station",
                    "lat": 51.5025,
                    "lon": -0.2801,
                    "modes": ["tube"],
                    "stopType": "NaptanMetroStation",
                },
            ]
        )

        south_west, north_east = compute_padded_bounds(
            stations,
            padding_ratio=0.1,
            min_padding_degrees=0.02,
        )

        self.assertLess(south_west["lat"], 51.5025)
        self.assertLess(south_west["lon"], -0.2801)
        self.assertGreater(north_east["lat"], 51.531926)
        self.assertGreater(north_east["lon"], 0.003737)


if __name__ == "__main__":
    unittest.main()
