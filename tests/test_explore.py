"""
Created on 2025-06-02

@author: wf
"""

import json
import logging

from ngwidgets.basetest import Basetest

from velorail.explore import Explorer, Node, TriplePos
from velorail.npq import NPQ_Handler


class TestExplorer(Basetest):
    """
    test explorer
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.handler = NPQ_Handler("sparql-explore.yaml")

    def test_explorer(self):
        """
        Test explorer with different endpoints and examples
        """
        # Define test cases for different endpoints
        endpoint_tests = {
            "osm": {
                "endpoints": ["osm-qlever", "osm-sophox"],
                "examples": {"cycle_route": {"prefix": "osmrel", "id": "10492086"}},
            },
            "wikidata": {
                "endpoints": ["wikidata", "wikidata-qlever"],
                "examples": {"Tim Berners-Lee": {"prefix": "wd", "id": "Q80"}},
            },
        }

        for _platform, config in endpoint_tests.items():
            for endpoint_name in config["endpoints"]:
                explorer = Explorer(endpoint_name)
                self.assertIsNotNone(explorer)

                # Test each example for this endpoint
                for example_name, example in config["examples"].items():
                    if self.debug:
                        print(f"\nTesting {example_name} on {endpoint_name}")

                    # Create start node
                    prefix = example["prefix"]
                    node_id = example["id"]
                    start_node = explorer.get_node(node_id=node_id, prefix=prefix)
                    # Get exploration results
                    for summary in (False, True):
                        lod = explorer.explore_node(
                            start_node, triple_pos=TriplePos.SUBJECT, summary=summary
                        )
                        if self.debug:
                            print(f"{len(lod)}")
                            debug_limit = 7 if summary else 9
                            debug_lod = lod[:debug_limit]
                            print(json.dumps(debug_lod, indent=2, default=str))

    def test_merge_prefixes(self):
        """
        Test merging of prefixes from different sources
        """
        # Test case 1: No duplicates
        query = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?p ?o
WHERE { ?s ?p ?o }"""

        endpoint_prefixes = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"""
        endpoint_prefix_dict, _body = self.handler.parse_prefixes(endpoint_prefixes)
        merged = self.handler.merge_prefixes(query, endpoint_prefix_dict)
        self.assertTrue("PREFIX rdfs:" in merged)
        self.assertTrue("PREFIX owl:" in merged)
        self.assertTrue("PREFIX xsd:" in merged)

        # Test case 2: With duplicates
        query2 = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?p ?o
WHERE { ?s ?p ?o }"""

        merged2 = self.handler.merge_prefixes(query2, endpoint_prefix_dict)
        # Count occurrences of each prefix
        self.assertEqual(merged2.count("PREFIX owl:"), 1)
        self.assertEqual(merged2.count("PREFIX rdfs:"), 1)

        # Test case 3: Empty endpoint prefixes
        merged3 = self.handler.merge_prefixes(query, {})
        self.assertEqual(merged3, query)

        # Test case 4: Query without prefixes
        query4 = "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        merged4 = self.handler.merge_prefixes(query4, endpoint_prefix_dict)
        self.assertTrue("PREFIX owl:" in merged4)
        self.assertTrue("PREFIX xsd:" in merged4)
        self.assertTrue("SELECT ?s" in merged4)
