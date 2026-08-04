"""
Created on 2026-08-04

@author: wf

Bounding box route lookup see
https://github.com/WolfgangFahl/velorail/issues/5
"""

from typing import Dict, List

from velorail.bbox import BBox
from velorail.npq import NPQ_Handler


class RouteFinder(NPQ_Handler):
    """
    Find OpenStreetMap route relations by bounding box
    """

    query_by_source: Dict[str, str] = {
        "train": "TrainRoutes4Bounds",
        "bike": "BikeRoutes4Bounds",
    }

    def __init__(self, debug: bool = False):
        """
        Constructor

        Args:
            debug: if True switch on debug mode
        """
        super().__init__("routes.yaml", debug=debug)

    def get_routes_by_bounds(
        self,
        source: str,
        bbox: BBox,
        endpoint: str = "osm-qlever",
        limit: int = 100,
    ) -> List[dict]:
        """
        Get the routes of the given source that intersect the bounding box.

        Args:
            source: "train" or "bike"
            bbox: the target bounding box
            endpoint: the name of the SPARQL endpoint to use
            limit: the maximum number of routes to return

        Returns:
            list: the list of dicts with the route records

        Raises:
            ValueError: if the source is unknown
        """
        query_name = self.query_by_source.get(source)
        if not query_name:
            sources = ",".join(self.query_by_source.keys())
            raise ValueError(f"invalid source {source} - use one of {sources}")
        param_dict = bbox.as_param_dict(limit=limit)
        lod = self.query_by_name(
            query_name=query_name,
            param_dict=param_dict,
            endpoint=endpoint,
        )
        for record in lod:
            record["source"] = source
        return lod

    def get_routes(
        self,
        sources: List[str],
        bbox: BBox,
        endpoint: str = "osm-qlever",
        limit: int = 100,
    ) -> List[dict]:
        """
        Get the routes of all given sources that intersect the bounding box.

        Args:
            sources: the list of sources e.g. ["train","bike"]
            bbox: the target bounding box
            endpoint: the name of the SPARQL endpoint to use
            limit: the maximum number of routes per source

        Returns:
            list: the list of dicts with the route records
        """
        lod = []
        for source in sources:
            lod.extend(
                self.get_routes_by_bounds(
                    source=source, bbox=bbox, endpoint=endpoint, limit=limit
                )
            )
        return lod
