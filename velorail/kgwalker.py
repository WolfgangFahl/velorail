"""
Knowledge Graph walker implementation
Created on 2025-02-13
@author: wf
"""

from typing import Any, Dict, List, Optional

from velorail.explore import Explorer, TriplePos
from velorail.querygen import QueryGen


class KGWalker:
    """
    Knowledge Graph walker that combines exploration, 
    query generation and result viewing
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
        Get the table of properties to be generated

        Args:
            query_lod (list): List of dictionaries containing query results
            selected_props (list): List of property IDs to select

        Returns:
            list: Generated list of dictionaries containing selected properties
        """
        seen_props = set()
        gen_lod = []
        # Collect selected properties from query results
        for record in query_lod:
            record_copy = record.copy()
            prop_value = record_copy.get("p")
            prop = self.explorer.get_prop(prop_value)
            if (
                prop
                and prop.pid in selected_props
                and prop.pid not in seen_props
                and "/direct/" in prop_value
            ):
                if self.debug:
                    print(
                        f"selecting {prop} with type_name {prop.type_name} from {record}"
                    )
                record_copy["wikidata_property"] = prop
                gen_lod.append(record_copy)
                seen_props.add(prop.pid)
        return gen_lod

    def explore_and_query(
        self, prefix: str, node_id: str, selected_props: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Explore the knowledge graph and generate/execute query from the given start node

        Args:
            prefix (str): the prefix to use e.g. wd
            node_id (str): the id of the node to start from
            selected_props (List[str]): list of properties to select e.g. ["named after", "P10689"]

        Returns:
            List[Dict[str, Any]]: List of raw query results
        """
        start_node = self.explorer.get_node(node_id, prefix)

        # Get exploration query results
        query_lod = self.explorer.explore_node(
            node=start_node, triple_pos=TriplePos.SUBJECT, summary=True
        )

        # Table of selected properties for generation
        gen_lod = self.get_gen_lod(query_lod, selected_props)

        # Generate query with selected properties
        generated_query = self.query_gen.gen(
            lod=gen_lod, main_var="item", main_value=start_node.qualified_name
        )

        if self.debug:
            print(generated_query)

        # Execute query and store results
        query_results = self.explorer.query(
            sparql_query=generated_query, param_dict={}, endpoint=self.endpoint_name
        )
        return query_results

    def create_view(
        self, query_results: List[Dict[str, Any]], depth: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Create a view record from query results

        Args:
            query_results (List[Dict[str, Any]]): List of raw query results
            depth (int): Depth for view record generation, defaults to 1

        Returns:
            Optional[Dict[str, Any]]: View record if results exist, None otherwise
        """
        view_record = None
        if len(query_results) >= 1:
            record = query_results[0]
            view_record = self.explorer.get_view_record(record, depth)
        return view_record

    def walk(
        self,
        prefix: str,
        node_id: str,
        selected_props: List[str],
        create_view: bool = True,
        view_depth: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """
        Walk the knowledge graph from the given start node

        Args:
            prefix (str): the prefix to use e.g. wd
            node_id (str): the id of the node to start from
            selected_props (List[str]): list of properties to select e.g. ["named after", "P10689"]
            create_view (bool): if True, generate a view record from results
            view_depth (int): depth for view record generation if create_view is True, defaults to 1

        Returns:
            Optional[Dict[str, Any]]: View record if create_view is True, raw query results otherwise
        """
        # Get query results
        query_results = self.explore_and_query(prefix, node_id, selected_props)

        # Prepare return value based on mode and results
        result = None
        if query_results:
            if create_view:
                result = self.create_view(query_results, view_depth)
            else:
                result = query_results

        return result
