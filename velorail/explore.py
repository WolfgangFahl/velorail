"""
SPARQL Graph Explorer - A tool for interactive exploration of RDF graphs
Created on 2025-02-06
@author: wf
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ez_wikidata.wdproperty import WikidataProperty, WikidataPropertyManager
from ngwidgets.widgets import Link

from velorail.npq import NPQ_Handler


class TriplePos(Enum):
    SUBJECT = "subject"
    PREDICATE = "predicate"
    OBJECT = "object"


@dataclass
class Node:
    """
    Represents a node in the RDF graph
    """

    prefix: str
    node_id: str
    uri: Optional[str] = None
    label: Optional[str] = None

    @property
    def qualified_name(self) -> str:
        """
        Returns the qualified name in the format {prefix}:{node_id}
        """
        return f"{self.prefix}:{self.node_id}"


class Explorer(NPQ_Handler):
    """
    A SPARQL explorer that allows traversing RDF graphs starting from any node
    """

    def __init__(self, endpoint_name: str):
        """
        Initialize the explorer with a SPARQL endpoint

        Args:
            endpoint_name: Name of the SPARQL endpoint to query as defined in endpoints.yaml
        """
        super().__init__("sparql-explore.yaml")
        self.endpoint_name = endpoint_name
        self.wpm = WikidataPropertyManager.get_instance()

    def get_prop(self, value: str) -> WikidataProperty:
        """
        Get the WikidataProperty for the given value string - either from a URI or direct property id

        Args:
            value (str): The value to check - either a URI or direct property id

        Returns:
            WikidataProperty: The property if found else None
        """
        prop = None
        if "wikidata" in self.endpoint_name and self.wpm:
            prop_pattern = r"P(\d+)"
            # Only try to extract pid if it's a property URI or matches P-number pattern
            if "www.wikidata.org/prop" in value or re.match(prop_pattern, value):
                pid = re.sub(f".*{prop_pattern}.*", r"P\1", value)
                if pid:
                    prop = self.wpm.get_property_by_id(pid)
        return prop

    def get_view_record(self, record: dict, index: int) -> dict:
        """
        get the view record for the given record

        Args:
            record (dict): The source record to convert
            index (int): The row index

        Returns:
            dict: The view record with formatted links and properties
        """
        view_record = {"#": index}  # Number first
        record_copy = record.copy()
        for key, value in record_copy.items():
            if isinstance(value, str):
                prop = self.get_prop(value)
                if prop:
                    view_record[key] = Link.create(
                        prop.url, f"{prop.plabel} ({prop.pid})"
                    )
                    continue
                if value.startswith("http"):
                    view_record[key] = Link.create(value, value)
            else:
                view_record[key] = value
        return view_record

    def get_node(self, node_id: str, prefix: str) -> Node:
        """
        Resolve a node URI using stored prefixes.

        Args:
            node_id (str): The node identifier.
            prefix (str): The prefix to resolve.

        Returns:
            Node: Constructed node with resolved URI.
        """
        endpoint_prefix_dict = self.endpoint_prefixes.get(self.endpoint_name, {})

        if prefix in endpoint_prefix_dict:
            base_uri = endpoint_prefix_dict[prefix]
            uri = f"{base_uri}{node_id}"
        else:
            raise ValueError(
                f"Prefix '{prefix}' not found in endpoint '{self.endpoint_name}'"
            )

        node = Node(
            uri=uri,
            prefix=prefix,
            node_id=node_id,
        )
        return node

    def explore_node(
        self, node: Node, triple_pos: TriplePos, summary: bool = False
    ) -> str:
        """
        Get the appropriate exploration query based on node type

        Args:
            node: The node to explore from
            triple_pos: The triple position
            summary: show a summary with counts

        Returns:
            Query result from the appropriate SPARQL query
        """
        query_map = {
            TriplePos.SUBJECT: (
                "ExploreFromSubject" if not summary else "ExploreFromSubjectSummary"
            ),
            TriplePos.PREDICATE: (
                "ExploreFromPredicate" if not summary else "ExploreFromPredicateSummary"
            ),
            TriplePos.OBJECT: (
                "ExploreFromObject" if not summary else "ExploreFromObjectSummary"
            ),
        }

        query_name = query_map[triple_pos]

        param_dict = {"start_node": node.qualified_name}

        lod = self.query_by_name(
            query_name=query_name, param_dict=param_dict, endpoint=self.endpoint_name
        )
        return lod
