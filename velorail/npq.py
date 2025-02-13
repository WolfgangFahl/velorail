"""
Created on 2025-02-06

@author: wf
"""

import logging
import re
from pathlib import Path

from lodstorage.query import EndpointManager, Query, QueryManager
from lodstorage.sparql import SPARQL, Params


class NPQ_Handler:
    """
    Handling of named parameterized queries
    """

    def __init__(self, yaml_file: str, with_default: bool = False, debug: bool = False):
        """
        Constructor

        Args:
            yaml_file (str): The YAML file containing the queries.
            with_default (bool): Whether to include default endpoints.
            debug(bool): if True switch on debug mode
        """

        self.debug = debug
        self.endpoint_path = Path(__file__).parent / "resources" / "endpoints.yaml"
        self.query_path = Path(__file__).parent / "resources" / "queries"
        self.query_yaml = self.query_path / yaml_file

        if not self.query_yaml.is_file():
            raise FileNotFoundError(f"Queries file not found: {self.query_yaml}")

        self.query_manager = QueryManager(
            lang="sparql", queriesPath=self.query_yaml.as_posix()
        )

        self.endpoints = EndpointManager.getEndpoints(
            self.endpoint_path.as_posix(), with_default=with_default
        )

        # Preload prefixes for each endpoint
        self.endpoint_prefixes = {}
        for endpoint_name, endpoint in self.endpoints.items():
            if hasattr(endpoint, "prefixes"):
                prefix_dict, _body = self.parse_prefixes(endpoint.prefixes)
                self.endpoint_prefixes[endpoint_name] = prefix_dict
            else:
                self.endpoint_prefixes[endpoint_name] = dict()

    def parse_prefixes(self, prefix_str: str) -> dict:
        """
        Parse prefixes from string with newlines and prefixes per
        line into a dictionary

        Args:
            prefix_str (str): The string containing prefix definitions.

        Returns:
            dict: A dictionary mapping prefix names to their URIs.
        """
        prefix_pattern = re.compile(
            r"^prefix\s+(?P<name>\w+):\s+<(?P<uri>[^>]+)>", re.IGNORECASE
        )
        prefix_dict = {}
        body = ""
        for line in prefix_str.splitlines():
            if match := prefix_pattern.match(line.strip()):
                name = match.group("name")
                uri = match.group("uri")
                prefix_dict[name] = uri
            else:
                body += line + "\n"
        return prefix_dict, body

    def to_set(self, prefix_dict) -> set:
        prefix_set = set()
        for name in prefix_dict.keys():
            prefix_set.add(name)
        return prefix_set

    def merge_prefixes_by_endpoint_name(
        self, query_str: str, endpoint_name: str
    ) -> str:
        """
        Merge query prefixes with endpoint prefixes avoiding duplicates.

        Args:
            query_str (str): SPARQL query string potentially containing prefixes.
            endpoint_name (str): Name of the endpoint to use for prefix lookup.

        Returns:
            str: Query with merged unique prefixes.
        """
        endpoint_prefix_dict = self.endpoint_prefixes.get(endpoint_name, {})
        merged_query = self.merge_prefixes(query_str, endpoint_prefix_dict)
        return merged_query

    def merge_prefixes(self, query_str: str, endpoint_prefix_dict: dict) -> str:
        """
        Merge query prefixes with endpoint prefixes avoiding duplicates.

        Args:
            query_str (str): SPARQL query string potentially containing prefixes.
            endpoint_prefix_dict (dict): Dictionary mapping prefix names to URIs.

        Returns:
            str: Query with merged unique prefixes.
        """
        prefix_dict, body_section = self.parse_prefixes(query_str)
        query_prefix_set = self.to_set(prefix_dict)

        endpoint_prefix_set = self.to_set(endpoint_prefix_dict)

        missing_prefixes = endpoint_prefix_set - query_prefix_set

        if not missing_prefixes:
            return query_str

        merged_prefix_dict = dict(endpoint_prefix_dict)
        merged_prefix_dict.update(prefix_dict)

        merged_prefix_lines = []
        for prefix in sorted(merged_prefix_dict.keys()):
            uri = merged_prefix_dict[prefix]
            merged_prefix_lines.append(f"PREFIX {prefix}: <{uri}>")

        merged_query = "\n".join(merged_prefix_lines) + f"\n\n{body_section}"
        return merged_query

    def query_by_name(
        self,
        query_name: str,
        param_dict: dict = {},
        endpoint: str = "wikidata-qlever",
        auto_prefix: bool = True,
    ):
        """
        Get the result of the given query.

        Args:
            query_name (str): Name of the query to execute.
            param_dict (dict): Dictionary of parameters to substitute.
            endpoint (str): Name of the endpoint to use.
            auto_prefix (bool): Whether to automatically add endpoint prefixes.

        Returns:
            list: List of dictionaries with query results.
        """
        query: Query = self.query_manager.queriesByName.get(query_name)
        if not query:
            raise ValueError(f"{query_name} is not defined!")

        # Get the query string and handle prefixes
        sparql_query = query.query
        lod = self.query(
            sparql_query=sparql_query,
            param_dict=param_dict,
            endpoint=endpoint,
            auto_prefix=auto_prefix,
        )
        return lod

    def query(
        self,
        sparql_query: str,
        param_dict: dict = {},
        endpoint: str = "wikidata-qlever",
        auto_prefix: bool = True,
    ):
        """
        Get the result of the given query.

        Args:
            sparql_query (str): the query to execute.
            param_dict (dict): Dictionary of parameters to substitute.
            endpoint (str): Name of the endpoint to use.
            auto_prefix (bool): Whether to automatically add endpoint prefixes.

        Returns:
            list: List of dictionaries with query results.
        """

        sparql_endpoint = self.endpoints[endpoint]
        endpoint_instance = SPARQL(sparql_endpoint.endpoint)

        if auto_prefix:
            logging.debug(f"Auto prefixing for endpoint: {endpoint}")
            sparql_query = self.merge_prefixes_by_endpoint_name(sparql_query, endpoint)
        msg = f"SPARQL query:\n{sparql_query}"
        logging.debug(msg)
        if self.debug:
            print(msg)
            params = Params(sparql_query)
            final_query = params.apply_parameters_with_check(param_dict)
            print("parameterized query:")
            print(final_query)

        # Execute query
        lod = endpoint_instance.queryAsListOfDicts(sparql_query, param_dict=param_dict)
        return lod
