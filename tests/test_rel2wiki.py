'''
Created on 2025-02-04

@author: wf
'''
import json
from velorail.locfind import NPQ_Handler
from velorail.rel2wiki import OsmRelConverter
from ngwidgets.basetest import Basetest
from argparse import Namespace

class QueryGen:
    """
    Generator for SPARQL queries based on property count query results.
    """

    def __init__(self, prefixes):
        """
        Initialize the QueryGen with a dictionary of prefixes.
        """
        self.prefixes = prefixes

    def sanitize_variable_name(self, prop):
        """
        Convert a prefixed prop into a valid SPARQL variable name.
        """
        parts = prop.split(":")
        var_name = ""
        if parts:
            var_name=parts[-1]
            for invalid in ["-",":","#"]:
                var_name = var_name.replace(invalid, "_")
        var_name=f"{var_name}"
        return var_name

    def get_prefixed_property(self, prop):
        """
        Convert a full URI into a prefixed SPARQL property if a matching prefix is found.
        """
        prefixed_prop = f"<{prop}>"
        for prefix, uri in self.prefixes.items():
            if prop.startswith(uri):
                prefixed_prop = prop.replace(uri, f"{prefix}:")
                break
        return prefixed_prop

    def gen(self, lod, main_var:str,main_value:str,first_x:int=5):
        """
        Generate a SPARQL query dynamically based on the lod results.
        """
        sparql_query="# generated Query"
        properties = {}
        for record in lod:
            if record["count"] == "1":
                prop=record["p"]
                prefixed_prop=self.get_prefixed_property(prop)
                var_name=self.sanitize_variable_name(prefixed_prop)
                properties[var_name]=prefixed_prop
        for key, value in self.prefixes.items():
            sparql_query+= f"\nPREFIX {key}: <{value}>"

        sparql_query += f"\nSELECT ?{main_var}"

        for i, var_name in enumerate(properties.keys()):
            comment="" if i < first_x else "#"
            sparql_query +=f"\n{comment}  ?{var_name}"

        sparql_query += "\nWHERE {\n"

        sparql_query += f"  VALUES (?{main_var}) {{ ({main_value}) }}\n"

        for i, (var_name,prefixed_prop) in enumerate(properties.items()):
            comment="" if i < first_x else "#"
            sparql_query += f"{comment} OPTIONAL {{ ?rel {prefixed_prop} ?{var_name} }} .\n"

        sparql_query += "}"  # Closing WHERE clause

        return sparql_query

class TestRel2wiki(Basetest):
    """
    test locfinder
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp_path="/tmp"
        self.query_handler=NPQ_Handler(yaml_file="osmplanet_explore.yaml")
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
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        }

    def testExplore(self):
        """
        test queries to explore correct OSM Planet SPAQRL queries
        """
        for query_name in [
            "Relation1",
            "RelationExplore"
        ]:
            lod=self.query_handler.query(
                query_name=query_name,
                param_dict={"relid":"10492086"},
                endpoint="osm-qlever")
            if self.debug:
                print(f"Query: {query_name}:")
                print(json.dumps(lod,indent=2))

    def testQueryGenPrefix(self):
        """
        test queries to explore correct OSM Planet SPAQRL queries
        """
        query_gen = QueryGen(self.prefixes)
        for prefix, prop in [
            ("osmkey", "ref"),
            ("meta", "uid"),
            ("rdf", "type"),
        ]:
            with self.subTest(prefix=prefix, prop=prop):
                prefix_uri = self.prefixes[prefix]
                long_prop = f"{prefix_uri}{prop}"
                short_prop = query_gen.get_prefixed_property(long_prop)
                expected = f"{prefix}:{prop}"
                self.assertEqual(short_prop, expected)

    def testQueryGenSanitize(self):
        """
        Test QueryGen functions for correct prefix handling and variable sanitization.
        """
        query_gen = QueryGen(self.prefixes)
        expected_results = {
            "osmkey:ref": "ref",
            "meta:uid": "uid",
            "rdf:type": "type",
        }

        for prop, expected in expected_results.items():
            with self.subTest(prop=prop):
                sanitized = query_gen.sanitize_variable_name(prop)
                self.assertEqual(sanitized, expected)


    def testQueryGen(self):
        """
        test generating a query
        """
        query_name = "RelationExplore"
        param_dict = {"relid": "10492086"}
        endpoint = "osm-qlever"

        lod = self.query_handler.query(query_name=query_name, param_dict=param_dict, endpoint=endpoint)
        if self.debug:
            print(f"Query: {query_name}:")
            print(json.dumps(lod, indent=2))
        query_gen = QueryGen(self.prefixes)
        relid=param_dict["relid"]
        value=f"osmrel:{relid}"
        sparql_query =query_gen.gen(lod,
            main_var="rel",
            main_value=value,
            first_x=9)

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
                #'2172017',
                '10492086',
                #'4220975'
            ],
            queriesPath=None,
            queryName="RelationNodesGeo"
        )

        # Create converter instance
        converter = OsmRelConverter(args=args)
        converter.test=True

        # Process the relations
        lod=converter.process_relations(args.relations)
        if self.debug:
            print(json.dumps(lod,indent=2))
