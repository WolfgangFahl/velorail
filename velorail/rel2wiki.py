#!/usr/bin/env python
import json
import os
from argparse import ArgumentParser, Namespace
from typing import Dict, List

from lodstorage.params import Params
from lodstorage.query import   QueryManager
from lodstorage.query_cmd import QueryCmd
from lodstorage.sparql import SPARQL

from velorail.locfind import LocFinder
from velorail.tour import LegStyles
from velorail.npq import NPQ_Handler


class OsmRelConverter:
    """
    Converter for OSM relations to MediaWiki pages
    """

    def __init__(self, args: Namespace):
        """
        Initialize the converter

        Args:
             args: command line args
        """
        self.args = args
        self.tmpdir = args.tmp
        self.query_handler=NPQ_Handler("osmplanet.yaml",debug=args.debug)
        self.leg_style = LegStyles.default()
        self.test = False

    @classmethod
    def get_parser(cls):
        """Get the argument parser"""
        parser = ArgumentParser(
            description="Convert OpenStreetMap railway relations to MediaWiki pages"
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
            "relations",
            nargs="*",
            default=["10492086", "4220975"],
            help="Relation IDs to process [default: %(default)s]",
        )
        args = parser.parse_args()
        if not args.queryName:
            args.queryName = "RelationNodesGeo"
        return args

    def query_rel(self, rel: str) -> Dict:
        """
        Query the given relation using SPARQL

        Args:
             rel: The relation ID to query

        Returns:
             Dict: The query results as list of dicts
        """
        param_dict = {
            "relid": rel,
            "role": self.args.role,
            "min_lat": str(self.args.min_lat),
            "max_lat": str(self.args.max_lat),
            "min_lon": str(self.args.min_lon),
            "max_lon": str(self.args.max_lon),
        }

        if self.args.debug:
            print(f"Querying relation {rel}")

        lod=self.query_handler.query_by_name(
            query_name=self.args.queryName,
            param_dict=param_dict,
            endpoint=self.args.endpoint_name,
            auto_prefix=True)
        return lod

    def to_mediawiki(self, rel: str, data: Dict) -> str:
        """
        Convert relation data to MediaWiki format

        Args:
             rel: Relation ID
             data: JSON data from query

        Returns:
             str: MediaWiki page content
        """
        wiki = f"""= Map =
https://www.openstreetmap.org/relation/{rel}
{{{{LegMap
|zoom={self.args.zoom}
}}}}

= Locs =
"""
        # Add locations
        for item in data:
            node_id = item["node"].split("/")[-1]
            loc = f"""{{{{Loc
|id={node_id}
|latlon={item["lat"]},{item["lon"]}
|name={item.get("node_name", node_id)}
|url=https://www.openstreetmap.org/node/{node_id}
|type=train_station
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
|transport=train
|storemode=subobject
}}}}
"""
                wiki += leg
            previous = item

        wiki += f"\n<headertabs/>\n[[Category:{self.args.category}]]"
        return wiki

    def process_relations(self, relations: List[str], with_write: bool = True):
        """
        Process the given relations

        Args:
             relations: List of relation IDs to process
        """
        for rel in relations:
            json_file = os.path.join(self.tmpdir, f"osm_{rel}.json")
            wiki_file = os.path.join(self.tmpdir, f"{rel}.wiki")

            if not self.test:
                print(f"Processing relation {rel}")

            # Query and save JSON
            data = self.query_rel(rel)
            if with_write:
                with open(json_file, "w") as f:
                    json.dump(data, f, indent=2)

            # Convert to wiki and save
            wiki = self.to_mediawiki(rel, data)
            if with_write:
                with open(wiki_file, "w") as f:
                    f.write(wiki)

            if not self.test:
                print(f"Created {wiki_file}")
        return data


def main():
    """Main entry point"""
    args = OsmRelConverter.get_parser()
    converter = OsmRelConverter(args=args)
    converter.process_relations(args.relations)


if __name__ == "__main__":
    main()
