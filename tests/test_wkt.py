"""
Created on 2025-02-12

@author: wf
"""
from ngwidgets.basetest import Basetest

from velorail.wkt import WKT


class TestWKT(Basetest):
    """
    Test WKT handling and conversions
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_wkt_to_latlon(self):
        """
        Test conversion of WKT to latlon or centroid
        """
        test_cases = [
            (
                "POINT(-3.319103 42.542723)",
                {"coords": (42.542723, -3.319103), "expected": ("42.542", "-3.319")},
            ),
            (
                "LINESTRING(-3.319103 42.542723, -3.319200 42.543000, -3.318900 42.543100)",
                {"coords": (42.542941, -3.319067), "expected": ("42.542", "-3.319")},
            ),
            (
                "POLYGON((-3.319103 42.542723, -3.319200 42.543000, -3.318900 42.543100, -3.319103 42.542723))",
                {"coords": (42.542941, -3.319067), "expected": ("42.542", "-3.319")},
            ),
        ]

        for wkt_str, test_data in test_cases:
            with self.subTest(wkt_str=wkt_str):
                wkt=WKT(wkt_str)
                lat, lon =wkt.to_latlon()
                e_lat, e_lon = test_data["coords"]
                e_lat_str, e_lon_str = test_data["expected"]
                self.assertAlmostEqual(lat, e_lat, places=4)
                self.assertAlmostEqual(lon, e_lon, places=4)
                latlon_str = wkt.to_latlon_str()
                if self.debug:
                    print(f"{latlon_str}")
                self.assertTrue(e_lat_str in latlon_str)
                self.assertTrue(e_lon_str in latlon_str)
