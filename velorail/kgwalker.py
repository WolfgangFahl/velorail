"""
Created on 2025-02-13

@author: wf
"""

from typing import List

from velorail.explore import Explorer, TriplePos
from velorail.querygen import QueryGen


class KGWalker:
    """
    Knowledge Graph walker that combines exploration, query generation and result viewing
    """

    def __init__(self, endpoint_name: str, debug: bool = False):
        """
        Initialize the KG walker

        Args:
            endpoint_name(str): the name of the endpoint to query
            debug(bool): if True show debug information
        """
        self.endpoint_name = endpoint_name
        self.debug = debug
        self.explorer = Explorer(endpoint_name)
        self.prefixes = self.explorer.endpoint_prefixes.get(endpoint_name)
        self.query_gen = QueryGen(prefixes=self.prefixes, debug=self.debug)

    def get_gen_lod(self, query_lod: list, selected_props: list) -> list:
        """
        get the table of properties to be generated
        """
        seen_props = set()
        gen_lod = []
        for record in query_lod:
            prop_value = record.get("p")
            prop = self.explorer.get_prop(prop_value)
            if prop and prop.pid in selected_props and prop.pid not in seen_props:
                if self.debug:
                    print(f"selecting {prop} from {record}")
                gen_lod.append(record)
                seen_props.add(prop.pid)
        return gen_lod

    def walk(self, prefix: str, node_id: str, selected_props: List[str]) -> dict:
        """
        Walk the knowledge graph from the given start node

        Args:
            prefix(str): the prefix to use e.g. wd
            node_id(str): the id of the node to start from
            selected_props: list of properties to select e.g. ["named after", "P10689"]

        Returns:
            dict: the view record of the properties found
        """
        start_node = self.explorer.get_node(node_id, prefix)
        # get exploration query results
        query_lod = self.explorer.explore_node(
            node=start_node, triple_pos=TriplePos.SUBJECT, summary=True
        )
        # table of selected properties for generation
        gen_lod = self.get_gen_lod(query_lod, selected_props)
        # generate query with selected properties
        generated_query = self.query_gen.gen(
            lod=gen_lod, main_var="item", main_value=start_node.qualified_name
        )
        if self.debug:
            print(generated_query)
        # run query
        lod = self.explorer.query(
            sparql_query=generated_query, param_dict={}, endpoint=self.endpoint_name
        )
        # we expect a single but long record
        if len(lod) >= 1:
            record = lod[0]
            # get view record
            view_record = self.explorer.get_view_record(record, 1)
            return view_record
        return None
