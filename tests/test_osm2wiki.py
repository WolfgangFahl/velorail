"""
Created on 2025-02-04

@author: wf
"""

import json
from argparse import Namespace
import os
from ngwidgets.basetest import Basetest
from velorail.locfind import NPQ_Handler
from velorail.osm2wiki import Osm2WikiConverter

class TestOsm2wiki(Basetest):
    """
    test  osm2wiki script
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp_path = "/tmp"
        self.query_handler = NPQ_Handler(yaml_file="osmplanet_explore.yaml",debug=self.debug)
        self.prefixes = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "geo": "http://www.opengis.net/ont/geosparql#",
            "geof": "http://www.opengis.net/def/function/geosparql/",
            "ogc": "http://www.opengis.net/rdf#",
            "osmkey": "https://www.openstreetmap.org/wiki/Key:",
            "osm2rdfmember": "https://osm2rdf.cs.uni-freiburg.de/rdf/member#",
            "osmrel": "https://www.openstreetmap.org/relation/",
            "osm2rdf": "https://osm2rdf.cs.uni-freiburg.de/rdf/",
            "osm2rdf_geom": "https://osm2rdf.cs.uni-freiburg.de/rdf/geom#",
            "meta": "https://www.openstreetmap.org/meta/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        }

    def testExplore(self):
        """
        test queries to explore correct OSM Planet SPAQRL queries
        """
        for query_name in ["Relation1", "RelationExplore"]:
            lod = self.query_handler.query_by_name(
                query_name=query_name,
                param_dict={"relid": "10492086"},
                endpoint="osm-qlever",
            )
            if self.debug:
                print(f"Query: {query_name}:")
                print(json.dumps(lod, indent=2))

    def testOsmRelConverter(self):
        """
        test the converter
        """
        for osm_item,role,transport,loc_type in [
            ("relation/1713826","member","bike","bike-waypoint"),
            ("relation/10492086","stop","train","train station")
        ]:
            args = Namespace(
                debug=self.debug,
                tmp=self.tmp_path,
                endpoint_name="osm-qlever",
                zoom=8,
                min_lat=42.0,
                max_lat=44.0,
                min_lon=-9.0,
                max_lon=4.0,
                transport=transport,
                loc_type=loc_type,
                role=role,
                country="Spanien",
                category="Spain2025",
                osm_items=[
                    osm_item
                ],
                queriesPath=None,
                queryName="ItemNodesGeo",
            )

            # Create converter instance
            converter = Osm2WikiConverter(args=args)
            converter.test = True

            # Process the relations
            lod = converter.process_osm_items(args.osm_items)
            if self.debug:
                print(f"{loc_type}:{osm_item}")
                print(json.dumps(lod, indent=2))
            self.assertTrue(os.path.exists(converter.wiki_file))
