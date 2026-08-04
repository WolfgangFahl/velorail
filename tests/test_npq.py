"""
Created on 2026-08-04

@author: wf
"""

from ngwidgets.basetest import Basetest

from velorail.locfind import LocFinder


class TestNPQ(Basetest):
    """
    Test the named parameterized query handling and the endpoint fallback
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_endpoint_chain(self):
        """
        test the fallback chain of an endpoint
        """
        locfinder = LocFinder()
        expected = ["wikidata-qlever", "wikidata-qlever-dbis", "wikidata"]
        self.assertEqual(expected, locfinder.endpoint_chain("wikidata-qlever"))
        # an endpoint without fallbacks stays alone
        self.assertEqual(["osm-qlever"], locfinder.endpoint_chain("osm-qlever"))

    def test_fallback_on_dead_primary(self):
        """
        test that a dead primary endpoint is bridged by its fallback
        """
        if Basetest.inPublicCI():
            return
        locfinder = LocFinder()
        locfinder.endpoints["wikidata-qlever"].endpoint = (
            "https://qlever.dev/api/does-not-exist"
        )
        wd_item = locfinder.get_wikidata_geo("Q300706")
        self.assertIsNotNone(wd_item)
        self.assertAlmostEqual(50.7677, wd_item.lat, places=3)
        self.assertAlmostEqual(6.0913, wd_item.lon, places=3)

    def test_all_endpoints_dead(self):
        """
        test that a failure is reported when no endpoint of the chain answers
        """
        if Basetest.inPublicCI():
            return
        locfinder = LocFinder()
        for endpoint_name in locfinder.endpoint_chain("wikidata-qlever"):
            locfinder.endpoints[endpoint_name].endpoint = (
                "https://qlever.dev/api/does-not-exist"
            )
        with self.assertRaises(RuntimeError) as context:
            locfinder.get_wikidata_geo("Q300706")
        message = str(context.exception)
        if self.debug:
            print(message)
        self.assertIn("all endpoints failed", message)
