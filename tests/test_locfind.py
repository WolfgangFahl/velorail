from velorail.locfind import LocFinder
from ngwidgets.basetest import Basetest

class TestLocFinder(Basetest):
    """
    test locfinder
    """

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
            "description": "railway station in Biarritz, France"
        }

        lod = locfinder.query(query_name="WikidataGeo", param_dict={"qid": qid})
        self.assertTrue(len(lod) >= 1)
        record = lod[0]

        # Check all fields are present with expected values
        for key, expected_value in expected.items():
            self.assertIn(key, record)
            if isinstance(expected_value, float):
                self.assertAlmostEqual(float(record[key]), expected_value, places=3)
            else:
                self.assertEqual(record[key], expected_value)

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


