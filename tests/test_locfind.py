import unittest

from velorail.locfind import LocFinder


class TestLocFinder(unittest.TestCase):
    """
    test locfinder
    """


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

if __name__ == '__main__':
    unittest.main()
