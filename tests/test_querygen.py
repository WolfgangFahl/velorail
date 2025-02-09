"""
Created on 2025-02-09

@author: wf
"""

from ngwidgets.basetest import Basetest

from velorail.explore import Explorer, TriplePos
from velorail.querygen import QueryGen


class TestQueryGen(Basetest):
    """
    test querygen  script
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.endpoint_name = "osm-qlever"
        self.explorer = Explorer(self.endpoint_name)
        prefixes = self.explorer.endpoint_prefixes.get(self.endpoint_name)
        self.query_gen = QueryGen(prefixes=prefixes, debug=self.debug)

    def test_gen_query(self):
        """
        Test SPARQL query generation.
        """
        main_var = "item"
        prefix = "osmrel"
        for node_id, expected_keys in [
            ("2172017", 24),
            ("10492086", 32)
        ]:
            with self.subTest(node_id=node_id):
                start_node = self.explorer.get_node(node_id, prefix)
                qlod = self.explorer.explore_node(
                    node=start_node, triple_pos=TriplePos.SUBJECT, summary=True
                )
                lod = []
                for record in qlod:
                    if record["count"] == "1":
                        lod.append(record)
                        #print (record)
                generated_query = self.query_gen.gen(
                    lod=lod,
                    main_var=main_var,
                    main_value=start_node.qualified_name,
                    first_x=10000,
                )
                if self.debug:
                    print(generated_query)
                lod=self.explorer.query(
                    sparql_query=generated_query,
                    param_dict={},
                    endpoint=self.endpoint_name
                )
                # we expect a single but long record
                self.assertEqual(len(lod),1)
                record=lod[0]
                self.assertEqual(len(record.keys()),expected_keys)
