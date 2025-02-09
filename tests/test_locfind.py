"""
Created on 2025-02-01

@author: th
"""

import json

from ngwidgets.basetest import Basetest

from velorail.locfind import LocFinder


class TestLocFinder(Basetest):
    """
    test locfinder
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_wikidata_loc(self):
        """
        test finding location of a wikidata item
        """
        locfinder = LocFinder()
        # Test with Gare de Biarritz (Q1959795)
        qid = "Q1959795"
        expected = {
            "lat": 43.4592,
            "lon": -1.5459,
            "label": "Gare de Biarritz",
            "description": "railway station in Biarritz, France",
        }

        lod = locfinder.query_by_name(query_name="WikidataGeo", param_dict={"qid": qid})
        self.assertTrue(len(lod) >= 1)
        record = lod[0]

        # Check all fields are present with expected values
        for key, expected_value in expected.items():
            self.assertIn(key, record)
            if isinstance(expected_value, float):
                self.assertAlmostEqual(float(record[key]), expected_value, places=3)
            else:
                self.assertEqual(record[key], expected_value)

    def test_wikidata_item_maps(self):
        """
        test WikidataGeoItem map link generation
        """
        locfinder = LocFinder()
        # Test with San Sebastian station (Q14314)
        qid = "Q14314"
        # Get the WikidataGeoItem
        wd_item = locfinder.get_wikidata_geo(qid)
        self.assertIsNotNone(wd_item)

        # Get map links
        map_links = wd_item.get_map_links()
        if self.debug:
            print(map_links)

    def test_get_train_stations(self):
        """
        test get_train_stations
        """
        locfinder = LocFinder()
        lod_train_stations = locfinder.get_all_train_stations()
        print(len(lod_train_stations))
        self.assertGreaterEqual(len(lod_train_stations), 70000)

    def test_get_nearest_train_station(self):
        """
        test get_nearest_train_station
        """
        lat = 43.2661645
        long = -1.9749167
        distance = 10
        locfinder = LocFinder()
        results = locfinder.get_train_stations_by_coordinates(lat, long, distance)
        print(results)
        self.assertGreaterEqual(len(results), 30)

    def test_get_bike_nodes_heeg_stavoren(self):
        """
        test getting bike nodes in the Heeg/Stavoren area of Friesland
        """
        # Bounding box for Heeg/Stavoren area
        south = 52.8349  # Southern boundary
        west = 5.3184  # Western boundary
        north = 53.0125  # Northern boundary
        east = 5.8279  # Eastern boundary

        locfinder = LocFinder()
        bike_routes = locfinder.get_bike_nodes_by_bounds(south, west, north, east)
        if self.debug:
            print(json.dumps(bike_routes, indent=2))
