"""
SPARQL Graph Explorer - A tool for interactive exploration of RDF graphs
Created on 2025-02-06
@author: wf
"""
from velorail.npq import NPQ_Handler
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    SUBJECT = "subject"
    PREDICATE = "predicate"
    OBJECT = "object"

@dataclass
class Node:
    """
    Represents a node in the RDF graph
    """
    uri: str
    value: str
    type: NodeType
    label: Optional[str] = None

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

    def explore_node(self, node: Node) -> str:
        """
        Get the appropriate exploration query based on node type

        Args:
            node: The node to explore from

        Returns:
            Query result from the appropriate SPARQL query
        """
        query_map = {
            NodeType.SUBJECT: "ExploreFromSubject",
            NodeType.PREDICATE: "ExploreFromPredicate",
            NodeType.OBJECT: "ExploreFromObject"
        }

        query_name = query_map[node.type]
        param_dict = {"start_node": node.uri}

        lod = self.query(
            query_name=query_name,
            param_dict=param_dict,
            endpoint=self.endpoint_name
        )
        return lod