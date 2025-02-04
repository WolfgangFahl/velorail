'''
Created on 2025-02-04

@author: wf
'''
import json
from velorail.rel2wiki import OsmRelConverter
from ngwidgets.basetest import Basetest
from argparse import Namespace
class TestRel2wiki(Basetest):
    """
    test locfinder
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp_path="/tmp"

    def testOsmRelConverter(self):
        """
        test the converter
        """
        args = Namespace(
            debug=self.debug,
            tmp=self.tmp_path,
            endpoint_name='osm-qlever',
            zoom=8,
            min_lat=42.0,
            max_lat=44.0,
            min_lon=-9.0,
            max_lon=4.0,
            role='stop',
            country='Spanien',
            category='Spain2025',
            relations=[
                '2172017',
                '10492086',
                #'4220975'
            ],
            queriesPath=None,
            queryName="RelationNodesGeo"
        )

        # Create converter instance
        converter = OsmRelConverter(args=args)

        # Process the relations
        converter.process_relations(args.relations)
