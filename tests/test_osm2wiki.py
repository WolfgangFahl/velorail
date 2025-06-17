"""
Created on 2025-02-04

@author: wf
"""

import json
import os
from argparse import Namespace

from ngwidgets.basetest import Basetest

from velorail.locfind import NPQ_Handler
from velorail.osm2wiki import Osm2WikiConverter


class TestOsm2wiki(Basetest):
    """
    test  osm2wiki script
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp_path = "/tmp"
        self.query_handler = NPQ_Handler(
            yaml_file="osmplanet_explore.yaml", debug=self.debug
        )
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

    def testCompressNodes(self):
        """
        Test node compression with different scenarios.
        """
        # Create a straight line of points spaced 500m apart
        points = [
            {"loc": f"POINT(2.0 {42.0 + (i * 0.004491)})", "node": f"node/{i}"}
            for i in range(10)
        ]

        args = Namespace(debug=True, tmp="/tmp")
        converter = Osm2WikiConverter(args=args)

        # Test cases: (input_points, min_distance_m, max_nodes, expected_count)
        for i, (input_points, min_distance_m, expected_count) in enumerate(
            [
                (points, 1000, 4),  # 1km spacing keeps every other point + last point
                (points, 2000, 2),  # 2km spacing keeps every fourth point + last point
                (
                    points,
                    100,
                    10,
                ),  # max_nodes limits to 4 points (last point may not be included)
                ([], 1000, 0),  # empty input
                ([points[0]], 1000, 1),  # single point
                (points[:2], 1000, 2),  # two points
            ]
        ):

            converter.set_wkts(input_points)
            compressed = converter.compress_nodes(
                input_points, min_distance_m=min_distance_m
            )
            self.assertEqual(len(compressed), expected_count, f"case {i}")

    def testOsmRelConverter(self):
        """
        test the converter
        """
        debug=self.debug
        #debug=True
        for osm_item, role, transport, loc_type, expected_nodes, min_node_distance in [
            ("relation/18343947", "member", "train", "train station",  53, 6000),
            ("relation/3421095" , "member", "bike",  "bike-waypoint",  29, 2000),
            ("relation/1713826" , "member", "bike",  "bike-waypoint",  10, 2500),
            ("relation/10492086", "stop"  , "train", "train station",  21, 8000),
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
                osm_items=[osm_item],
                queriesPath=None,
                queryName="ItemNodesGeo",
                min_node_distance=min_node_distance,
            )
            # Create converter instance
            converter = Osm2WikiConverter(args=args)
            converter.test = True

            # Process the relations
            lod = converter.process_osm_items(args.osm_items)
            node_count=len(lod)
            if debug:
                print(f"{loc_type}:{osm_item} {node_count} nodes")
                print(json.dumps(lod, indent=2, default=str))
                print(f"{loc_type}:{osm_item} {node_count} nodes expected: {expected_nodes}")

            self.assertTrue(node_count >= expected_nodes,node_count)
            self.assertTrue(os.path.exists(converter.wiki_file))
