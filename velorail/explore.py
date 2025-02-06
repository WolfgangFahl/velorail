"""
SPARQL Graph Explorer - A tool for interactive exploration of RDF graphs
Created on 2025-02-06
@author: wf
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    uri: Optional[str]= None
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

    def explore_node(self, node: Node, triple_pos:TriplePos, summary: bool = False) -> str:
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

        param_dict = {"start_node": node.qualified_name }

        lod = self.query(
            query_name=query_name, param_dict=param_dict, endpoint=self.endpoint_name
        )
        return lod
