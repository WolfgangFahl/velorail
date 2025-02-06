"""
Created on 2025-02-06

@author: wf
"""
from pathlib import Path
from lodstorage.query import EndpointManager, Query, QueryManager
from lodstorage.sparql import SPARQL
import logging

class NPQ_Handler():
    """
    handling of named parameterized queries
    """
    def __init__(self,yaml_file:str,with_default:bool=False):
        """
        constructor
        """
        self.endpoint_path = Path(__file__).parent / "resources" / "endpoints.yaml"
        self.query_path = Path(__file__).parent / "resources" / "queries"
        self.query_yaml= self.query_path / yaml_file
        if not self.query_yaml.is_file():
            raise FileNotFoundError(f"queries file not found: {self.query_yaml}")
        self.query_manager = QueryManager(
            lang="sparql", queriesPath=self.query_yaml.as_posix()
        )
        self.endpoints = EndpointManager.getEndpoints(
            self.endpoint_path.as_posix(),
            with_default=with_default)

    def merge_prefixes(self, query_str: str, endpoint_prefixes: str) -> str:
        """
        Merge query prefixes with endpoint prefixes avoiding duplicates

        Args:
            query_str(str): SPARQL query string potentially containing prefixes
            endpoint_prefixes(str): Prefix definitions from endpoint

        Returns:
            str: Query with merged unique prefixes
        """
        query_prefixes = set()
        endpoint_prefix_set = set()

        # Extract prefixes from query
        query_lines = query_str.split('\n')
        query_body = []
        for line in query_lines:
            line_stripped = line.strip()
            if line_stripped.lower().startswith('prefix'):
                query_prefixes.add(line_stripped)
            else:
                query_body.append(line)

        # Extract prefixes from endpoint
        if endpoint_prefixes:
            for line in endpoint_prefixes.split('\n'):
                line_stripped = line.strip()
                if line_stripped.lower().startswith('prefix'):
                    endpoint_prefix_set.add(line_stripped)

        # Find unique endpoint prefixes
        missing_prefixes = endpoint_prefix_set - query_prefixes

        all_prefixes = query_prefixes | missing_prefixes

        # Only rebuild if we have new prefixes to add
        if missing_prefixes:
            prefix_section = "\n".join(sorted(all_prefixes))
            body_section = "\n".join(query_body).strip()
            merged_query = f"{prefix_section}\n\n{body_section}"
        else:
            merged_query = query_str

        return merged_query

    def query(self,
             query_name: str,
             param_dict: dict = {},
             endpoint: str = "wikidata-qlever",
             auto_prefix: bool = True):
        """
        get the result of the given query

        Args:
            query_name(str): name of the query to execute
            param_dict(dict): dictionary of parameters to substitute
            endpoint(str): name of the endpoint to use
            auto_prefix(bool): whether to automatically add endpoint prefixes

        Returns:
            list: list of dictionaries with query results
        """
        query: Query = self.query_manager.queriesByName.get(query_name)
        if not query:
            raise ValueError(f"{query_name} is not defined!")

        sparql_endpoint = self.endpoints[endpoint]
        endpoint_instance = SPARQL(sparql_endpoint.endpoint)

        # Get the query string and handle prefixes
        sparql_query = query.query
        if auto_prefix and hasattr(sparql_endpoint, 'prefixes'):
            logging.debug(f"auto prefixing:\n{sparql_endpoint.prefixes}")
            sparql_query = self.merge_prefixes(sparql_query, sparql_endpoint.prefixes)
        logging.debug(f"SPARQL query:\n{sparql_query}")

        # Execute query
        lod = endpoint_instance.queryAsListOfDicts(sparql_query, param_dict=param_dict)
        return lod
