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
        lod = locfinder.query(query_name="WikidataGeo", param_dict={"qid": qid})
        self.assertTrue(len(lod) >= 1)
        record = lod[0]
        # Expected coordinates for Gare de Biarritz
        self.assertIn("lat", record)
        self.assertIn("lon", record)
        lat = float(record["lat"])
        lon = float(record["lon"])
        self.assertAlmostEqual(lat, 43.4592, places=3)
        self.assertAlmostEqual(lon, -1.5459, places=3)

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


