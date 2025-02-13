"""
Created on 2025-02-09

@author: wf
"""

import json

from ngwidgets.basetest import Basetest

from velorail.explore import Explorer, TriplePos
from velorail.npq import NPQ_Handler
from velorail.querygen import QueryGen


class TestQueryGen(Basetest):
    """
    test SPARQL Query Generator for explorer
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
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
        sparql_query = query_gen.gen(
            lod,
            main_var="rel",
            main_value=value,
            first_x=9,
            max_cardinality=1,
            comment_out=True,
        )

        if self.debug:
            print("Generated SPARQL Query:")
            print(sparql_query)

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

    def test_gen_query(self):
        """
        Test SPARQL query generation.
        """
        for (
            title,
            main_var,
            prefix,
            node_id,
            endpoint_name,
            first_x,
            comment_out,
            expected_keys,
        ) in [
            (
                "Vía Verde (Burgos - Túnel de La Engaña)",
                "bike_route",
                "osmrel",
                "2172017",
                "osm-qlever",
                1000,
                False,
                24,
            ),
            (
                "MD 18061",
                "train_route",
                "osmrel",
                "10492086",
                "osm-qlever",
                1000,
                False,
                32,
            ),
            (
                "Christian Ronaldo",
                "person",
                "wd",
                "Q11571",
                "wikidata-qlever",
                5,
                False,
                1,
            ),
        ]:
            with self.subTest(node_id=node_id):
                explorer = Explorer(endpoint_name)
                prefixes = explorer.endpoint_prefixes.get(endpoint_name)
                query_gen = QueryGen(prefixes=prefixes, debug=self.debug)
                start_node = explorer.get_node(node_id, prefix)
                qlod = explorer.explore_node(
                    node=start_node, triple_pos=TriplePos.SUBJECT, summary=True
                )
                generated_query = query_gen.gen(
                    lod=qlod,
                    main_var=main_var,
                    main_value=start_node.qualified_name,
                    max_cardinality=1,
                    first_x=first_x,
                    comment_out=comment_out,
                )
                if self.debug:
                    print(generated_query)
                lod = explorer.query(
                    sparql_query=generated_query, param_dict={}, endpoint=endpoint_name
                )
                # we expect a single but long record
                self.assertEqual(len(lod), 1)
                record = lod[0]
                if self.debug:
                    print(title)
                    print(json.dumps(record, indent=2, default=str))
                self.assertEqual(len(record.keys()), expected_keys)
