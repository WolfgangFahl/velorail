"""
Created on 2026-08-04

@author: wf
"""

from ngwidgets.basetest import Basetest

from velorail.bbox import BBox
from velorail.routefind import RouteFinder


class TestRouteFinder(Basetest):
    """
    Test the bounding box route lookup see
    https://github.com/WolfgangFahl/velorail/issues/5
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # Aachen city center
        self.aachen = BBox(south=50.75, west=6.05, north=50.80, east=6.12)

    def test_invalid_source(self):
        """
        test that an unknown source is rejected
        """
        route_finder = RouteFinder()
        with self.assertRaises(ValueError) as context:
            route_finder.get_routes_by_bounds(source="plane", bbox=self.aachen)
        if self.debug:
            print(context.exception)

    def test_routes_by_bounds(self):
        """
        test finding train and bike routes for a bounding box
        """
        if Basetest.inPublicCI():
            return
        expected_refs = {"train": "RE18", "bike": "EV3"}
        route_finder = RouteFinder()
        route_finder.debug = self.debug
        for source, expected_ref in expected_refs.items():
            lod = route_finder.get_routes_by_bounds(
                source=source, bbox=self.aachen, limit=100
            )
            if self.debug:
                print(f"{source}: {len(lod)} routes")
            self.assertTrue(len(lod) > 0)
            refs = [record.get("ref") for record in lod]
            self.assertIn(expected_ref, refs)
            for record in lod:
                self.assertEqual(source, record["source"])

    def test_routes(self):
        """
        test finding routes of multiple sources at once
        """
        if Basetest.inPublicCI():
            return
        route_finder = RouteFinder()
        lod = route_finder.get_routes(
            sources=["train", "bike"], bbox=self.aachen, limit=10
        )
        sources = {record["source"] for record in lod}
        self.assertEqual({"train", "bike"}, sources)
        self.assertEqual(20, len(lod))
