"""
Created on 2026-08-04

@author: wf
"""

from pathlib import Path

from ngwidgets.basetest import Basetest

from velorail.bbox import BBox
from velorail.gpx import GpxRoutes


class TestBBox(Basetest):
    """
    Test bounding box handling and the gpx bounding box view
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples_path = Path(__file__).parent.parent / "velorail_examples"
        # Aachen city center
        self.aachen = BBox(south=50.75, west=6.05, north=50.80, east=6.12)

    def gpx_routes(self, file_name: str) -> GpxRoutes:
        """
        Get the routes of the given example gpx file.

        Args:
            file_name: the name of the example file

        Returns:
            GpxRoutes: the routes of the example
        """
        gpx_path = self.examples_path / file_name
        gpx_routes = GpxRoutes.of_text(gpx_path.read_text(), source=file_name)
        return gpx_routes

    def test_invalid_bounds(self):
        """
        test that invalid bounds are rejected
        """
        invalid_cases = [
            {"south": 91.0, "west": 6.0, "north": 92.0, "east": 6.1},
            {"south": 50.0, "west": -181.0, "north": 51.0, "east": 6.1},
            {"south": 51.0, "west": 6.0, "north": 50.0, "east": 6.1},
            {"south": 50.0, "west": 6.2, "north": 51.0, "east": 6.1},
        ]
        for invalid_case in invalid_cases:
            with self.assertRaises(ValueError) as context:
                BBox(**invalid_case)
            if self.debug:
                print(f"{invalid_case}: {context.exception}")

    def test_wkt_and_center(self):
        """
        test the wkt markup and the center of a bounding box
        """
        wkt = self.aachen.as_wkt()
        if self.debug:
            print(wkt)
        self.assertTrue(wkt.startswith("POLYGON"))
        # wkt is in lon lat order
        self.assertIn("6.12 50.75", wkt)
        lat, lon = self.aachen.center
        self.assertAlmostEqual(50.775, lat, places=5)
        self.assertAlmostEqual(6.085, lon, places=5)

    def test_param_dict(self):
        """
        test the query parameters of a bounding box
        """
        param_dict = self.aachen.as_param_dict(limit=7)
        expected = {
            "south": 50.75,
            "west": 6.05,
            "north": 50.80,
            "east": 6.12,
            "limit": 7,
        }
        self.assertEqual(expected, param_dict)

    def test_overlap_and_containment(self):
        """
        test overlap and containment of bounding boxes
        """
        inside = BBox(south=50.77, west=6.08, north=50.78, east=6.09)
        touching = BBox(south=50.70, west=6.00, north=50.75, east=6.05)
        outside = BBox(south=51.00, west=7.00, north=51.10, east=7.10)
        self.assertTrue(inside.overlaps(self.aachen))
        self.assertTrue(inside.is_within(self.aachen))
        self.assertTrue(touching.overlaps(self.aachen))
        self.assertFalse(touching.is_within(self.aachen))
        self.assertFalse(outside.overlaps(self.aachen))
        self.assertFalse(outside.is_within(self.aachen))
        self.assertTrue(inside.matches(self.aachen, mode="contained"))
        self.assertFalse(touching.matches(self.aachen, mode="contained"))
        with self.assertRaises(ValueError):
            inside.matches(self.aachen, mode="invalid")

    def test_of_latlons(self):
        """
        test getting the bounding box of a list of coordinates
        """
        self.assertIsNone(BBox.of_latlons([]))
        latlons = [(50.7753, 6.0839), (50.7815, 6.1006), (50.7679, 6.0912)]
        bbox = BBox.of_latlons(latlons)
        expected = BBox(south=50.7679, west=6.0839, north=50.7815, east=6.1006)
        self.assertEqual(expected, bbox)

    def test_gpx_examples(self):
        """
        test the bounding boxes of the example gpx files
        """
        expected_routes = {
            "aachen_bike_loop.gpx": ("Aachen city loop", 6),
            "vennbahn_leg.gpx": ("Rothe Erde - Kornelimuenster", 4),
        }
        for file_name, expected in expected_routes.items():
            expected_name, expected_points = expected
            gpx_routes = self.gpx_routes(file_name)
            self.assertEqual(1, len(gpx_routes.routes))
            route = gpx_routes.routes[0]
            if self.debug:
                print(f"{file_name}: {route}")
            self.assertEqual(expected_name, route.name)
            self.assertEqual("track", route.kind)
            self.assertEqual(expected_points, route.point_count)

    def test_gpx_routes_in_bbox(self):
        """
        test finding gpx routes overlapping or contained in a bounding box
        """
        loop = self.gpx_routes("aachen_bike_loop.gpx")
        vennbahn = self.gpx_routes("vennbahn_leg.gpx")
        self.assertEqual(1, len(loop.routes_in_bbox(self.aachen)))
        self.assertEqual(1, len(loop.routes_in_bbox(self.aachen, mode="contained")))
        # the Vennbahn leg reaches into the box but leaves it to the south east
        self.assertEqual(1, len(vennbahn.routes_in_bbox(self.aachen)))
        self.assertEqual(0, len(vennbahn.routes_in_bbox(self.aachen, mode="contained")))

    def test_invalid_gpx(self):
        """
        test the handling of invalid gpx markup and urls
        """
        with self.assertRaises(ValueError):
            GpxRoutes.of_text("this is not gpx markup")
        with self.assertRaises(ValueError):
            GpxRoutes.of_url("file:///etc/passwd")
