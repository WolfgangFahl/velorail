#!/usr/bin/env python
import json
import os
import dataclasses
from argparse import ArgumentParser, Namespace
from typing import Dict, List

from lodstorage.query_cmd import QueryCmd

from velorail.npq import NPQ_Handler
from velorail.tour import LegStyles
from velorail.wkt import WKT


class Osm2WikiConverter:
    """
    Converter for OSM relations and nodes to MediaWiki pages
    """

    def __init__(self, args: Namespace):
        """
        Initialize the converter

        Args:
             args: command line args
        """
        self.args = args
        self.tmpdir = args.tmp
        self.query_handler = NPQ_Handler("osmplanet.yaml", debug=args.debug)
        self.leg_style = LegStyles.default()
        self.test = False

    @classmethod
    def get_parser(cls):
        """Get the argument parser"""
        parser = ArgumentParser(
            description="Convert OpenStreetMap relations and nodes to MediaWiki pages"
        )
        # Add standard query command args
        QueryCmd.add_args(parser)
        # Add our specific args
        parser.add_argument(
            "--tmp", default="/tmp", help="Temporary directory (default: %(default)s)"
        )
        parser.add_argument(
            "-en",
            "--endpoint_name",
            default="osm-qlever",
            help="Endpoint name (default: %(default)s)",
        )
        parser.add_argument(
            "--zoom", type=int, default=8, help="Zoom factor (default: %(default)s)"
        )
        parser.add_argument(
            "--min_lat",
            type=float,
            default=42.0,
            help="Minimum latitude (default: %(default)s)",
        )
        parser.add_argument(
            "--max_lat",
            type=float,
            default=44.0,
            help="Maximum latitude (default: %(default)s)",
        )
        parser.add_argument(
            "--min_lon",
            type=float,
            default=-9.0,
            help="Minimum longitude (default: %(default)s)",
        )
        parser.add_argument(
            "--max_lon",
            type=float,
            default=4.0,
            help="Maximum longitude (default: %(default)s)",
        )
        parser.add_argument(
            "--min_node_distance",
            type=float,
            default=1000,
            help="Minimum distance between nodes in m (default: 1000)",
        )
        parser.add_argument(
            "--role",
            default="stop",
            help="Member role to filter (default: %(default)s)",
        )
        parser.add_argument(
            "--country",
            default="Spanien",
            help="Country name for Loc template (default: %(default)s)",
        )
        parser.add_argument(
            "--category",
            default="Spain2025",
            help="Wiki category (default: %(default)s)",
        )
        parser.add_argument(
            "--loc_type",
            default="osm_node",
            help="location type (default: %(default)s)",
        )
        parser.add_argument(
            "--transport",
            default="bike",
            help="transport (default: %(default)s)",
        )
        parser.add_argument(
            "--osm_items",
            nargs="*",
            default=[
                "relation/10492086",
                "relation/4220975",
                "relation/1713826",
                "node/11757382798",
            ],
            help="osm items to process [default: %(default)s]",
        )
        args = parser.parse_args()
        return args

    def query_osm_item(self, osm_item: str) -> Dict:
        """
        Query the given osm_item using SPARQL

        Args:
             osm_item: The osm_item to query

        Returns:
             Dict: The query results as list of dicts
        """
        if osm_item.startswith("relation"):
            queryName = "ItemNodesGeo"
            id_key = "relid"
            osm_id = osm_item.replace("relation/", "")
        elif osm_item.startswith("node"):
            queryName = "NodeGeo"
            id_key = "osm_id"
            osm_id = osm_item.replace("node/", "")
        else:
            raise ValueError(f"invalid osm_item {osm_item}")

        param_dict = {
            id_key: osm_id,
            "role": self.args.role,
            "min_lat": str(self.args.min_lat),
            "max_lat": str(self.args.max_lat),
            "min_lon": str(self.args.min_lon),
            "max_lon": str(self.args.max_lon),
        }

        if self.args.debug:
            print(f"Querying osm_item {osm_item}")

        lod = self.query_handler.query_by_name(
            query_name=queryName,
            param_dict=param_dict,
            endpoint=self.args.endpoint_name,
            auto_prefix=True,
        )
        return lod

    def compress_nodes(
        self, nodes: List[Dict], min_distance_m: float = 1000
    ) -> List[Dict]:
        """
        Compress nodes by removing ones
        that are too close together using haversine distance.

        Args:
            nodes: List of node data dicts
            min_distance_m: Minimum distance between nodes in meters

        Returns:
            List[Dict]: Filtered node data
        """
        if not nodes or len(nodes) <= 2:
            return nodes

        compressed_nodes = []
        last_lat, last_lon = None, None

        for node in nodes:
            wkt_node=node["wkt"]
            # get a copy
            wkt=dataclasses.replace(wkt_node)
            points = wkt.to_latlon_list()  # Extract all points from LINESTRING

            for lat, lon in points:
                if (
                    last_lat is None
                    or WKT.distance(last_lat, last_lon, lat, lon) >= min_distance_m
                ):
                    # keep reference
                    wkt.lat = lat
                    wkt.lon = lon
                    compressed_nodes.append(node)
                    last_lat, last_lon = lat, lon  # Update last kept point
                    break  # Move to the next node after selecting the first valid point

        return compressed_nodes

    def set_wkts(self, nodes: List[Dict]):
        """
        Convert loc entries to WKT instances for each node

        Args:
            nodes: List of node data dicts

        """
        for node in nodes:
            node["wkt"] = WKT(node["loc"])

    def to_mediawiki(self, osm_item: str, data: Dict) -> str:
        """
        Convert relation data to MediaWiki format

        Args:
             osm_item: Relation ID
             data: JSON data from query

        Returns:
             str: MediaWiki page content
        """
        wiki = f"""= Map =
https://www.openstreetmap.org/{osm_item}
{{{{LegMap
|zoom={self.args.zoom}
}}}}

= Locs =
"""
        # Add locations
        for item in data:
            node = item["node"]
            node_id = node.split("/")[-1]
            wkt = item["wkt"]
            latlon = wkt.to_latlon_str()
            name = item.get("node_name", node_id)
            loc = f"""{{{{Loc
|id={node_id}
|latlon={latlon}
|name={name}
|url={node}
|type={self.args.loc_type}
|address={self.args.country}
|storemode=subobject
}}}}
"""
            wiki += loc

        # Add legs
        wiki += "\n= Legs =\n"
        previous = None
        for item in data:
            if previous:
                leg = f"""{{{{Leg
|wp_num={item["rel_pos"]}
|from={previous["node"].split("/")[-1]}
|to={item["node"].split("/")[-1]}
|transport={self.args.transport}
|storemode=subobject
}}}}
"""
                wiki += leg
            previous = item

        wiki += f"\n<headertabs/>\n[[Category:{self.args.category}]]"
        return wiki

    def process_osm_items(self, osm_items: List[str], with_write: bool = True):
        """
        Process the given osm_items

        Args:
             osm_items: List of osm_items to process
             e.g. relation/<osm_id> or node/<osm_id>
        """
        for osm_item in osm_items:
            base_name = osm_item.replace("/", "_")
            json_file = os.path.join(self.tmpdir, f"osm_{base_name}.json")
            self.wiki_file = os.path.join(self.tmpdir, f"{base_name}.wiki")

            if not self.test:
                print(f"Processing osm item {osm_item}")

            # Query and save JSON
            q_data = self.query_osm_item(osm_item)
            if with_write:
                with open(json_file, "w") as f:
                    json.dump(q_data, f, indent=2)

            self.set_wkts(q_data)
            if self.args.min_node_distance:
                c_data = self.compress_nodes(
                    q_data, min_distance_m=self.args.min_node_distance
                )
            else:
                c_data = q_data

            # Convert to wiki and save
            wiki = self.to_mediawiki(osm_item, c_data)
            if with_write:
                with open(self.wiki_file, "w") as f:
                    f.write(wiki)

            if not self.test:
                print(f"Created {self.wiki_file}")
        return c_data


def main():
    """Main entry point"""
    args = Osm2WikiConverter.get_parser()
    converter = Osm2WikiConverter(args=args)
    converter.process_osm_items(args.osm_items)


if __name__ == "__main__":
    main()
