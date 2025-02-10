"""
Created on 2025-02-09

@author: wf
"""
import json
from ngwidgets.basetest import Basetest

from velorail.explore import Explorer, TriplePos
from velorail.querygen import QueryGen


class TestQueryGen(Basetest):
    """
    test SPARQL Query Generator for explorer
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_gen_query(self):
        """
        Test SPARQL query generation.
        """
        for title,main_var,prefix,node_id, endpoint_name,first_x,comment_out,expected_keys in [
            ("Vía Verde (Burgos - Túnel de La Engaña)","bike_route","osmrel","2172017","osm-qlever",1000,False, 24),
            ("MD 18061","train_route","osmrel","10492086","osm-qlever",1000,False, 32),
            ("Christian Ronaldo","person","wd","Q11571","wikidata-qlever",5,False, 1)
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
                    comment_out=comment_out
                )
                if self.debug:
                    print(generated_query)
                lod=explorer.query(
                    sparql_query=generated_query,
                    param_dict={},
                    endpoint=endpoint_name
                )
                # we expect a single but long record
                self.assertEqual(len(lod),1)
                record=lod[0]
                if self.debug:
                    print(title)
                    print(json.dumps(record,indent=2,default=str))
                self.assertEqual(len(record.keys()),expected_keys)
