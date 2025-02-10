"""
Created on 2025-02-04

@author: wf
"""

import json
from argparse import Namespace

from ngwidgets.basetest import Basetest
from velorail.querygen import QueryGen
from velorail.locfind import NPQ_Handler
from velorail.rel2wiki import OsmRelConverter

class TestRel2wiki(Basetest):
    """
    test  rel2wiki script
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


    def testQueryGen(self):
        """
        test generating a query
        """
        query_name = "RelationExplore"
        param_dict = {"relid": "10492086"}
        endpoint = "osm-qlever"

        lod = self.query_handler.query_by_name(
            query_name=query_name, param_dict=param_dict, endpoint=endpoint
        )
        if self.debug:
            print(f"Query: {query_name}:")
            print(json.dumps(lod, indent=2))
        query_gen = QueryGen(self.prefixes)
        relid = param_dict["relid"]
        value = f"osmrel:{relid}"
        sparql_query = query_gen.gen(lod,
            main_var="rel",
            main_value=value,
            first_x=9,
            max_cardinality=1,
            comment_out=True)

        if self.debug:
            print("Generated SPARQL Query:")
            print(sparql_query)

    def testOsmRelConverter(self):
        """
        test the converter
        """
        args = Namespace(
            debug=self.debug,
            tmp=self.tmp_path,
            endpoint_name="osm-qlever",
            zoom=8,
            min_lat=42.0,
            max_lat=44.0,
            min_lon=-9.0,
            max_lon=4.0,
            role="stop",
            country="Spanien",
            category="Spain2025",
            relations=[
                #'2172017',
                "10492086",
                #'4220975'
            ],
            queriesPath=None,
            queryName="RelationNodesGeo",
        )

        # Create converter instance
        converter = OsmRelConverter(args=args)
        converter.test = True

        # Process the relations
        lod = converter.process_relations(args.relations)
        if self.debug:
            print(json.dumps(lod, indent=2))
