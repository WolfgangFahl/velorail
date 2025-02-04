#!/usr/bin/env python
from argparse import ArgumentParser, Namespace
import os
import json
from typing import Dict, List

from lodstorage.query import EndpointManager, QueryManager
from lodstorage.sparql import SPARQL
from lodstorage.query_cmd import QueryCmd
from lodstorage.params import Params
from velorail.tour import LegStyles
from velorail.locfind import LocFinder

class OsmRelConverter:
    """
    Converter for OSM relations to MediaWiki pages
    """

    def __init__(self, args:Namespace):
        """
        Initialize the converter

        Args:
             args: command line args
        """
        self.args = args
        self.tmpdir = args.tmp
        self.loc_finder=LocFinder()
        self.endpoints = self.loc_finder.endpoints
        self.endpoint = self.endpoints.get(args.endpoint_name)
        self.sparql = SPARQL.fromEndpointConf(self.endpoint)
        self.leg_style=LegStyles.default()

    @classmethod
    def get_parser(cls):
        """Get the argument parser"""
        parser = ArgumentParser(description="Convert OpenStreetMap railway relations to MediaWiki pages")
        # Add standard query command args
        QueryCmd.add_args(parser)
        # Add our specific args
        parser.add_argument('--tmp', default='/tmp', help='Temporary directory (default: %(default)s)')
        parser.add_argument('-en', '--endpoint_name', default='osm-qlever',
            help='Endpoint name (default: %(default)s)')
        parser.add_argument('--zoom', type=int, default=8,
            help='Zoom factor (default: %(default)s)')
        parser.add_argument('--min_lat', type=float, default=42.0,
            help='Minimum latitude (default: %(default)s)')
        parser.add_argument('--max_lat', type=float, default=44.0,
            help='Maximum latitude (default: %(default)s)')
        parser.add_argument('--min_lon', type=float, default=-9.0,
            help='Minimum longitude (default: %(default)s)')
        parser.add_argument('--max_lon', type=float, default=4.0,
            help='Maximum longitude (default: %(default)s)')
        parser.add_argument('--role', default='stop',
            help='Member role to filter (default: %(default)s)')
        parser.add_argument('--country', default='Spanien',
            help='Country name for Loc template (default: %(default)s)')
        parser.add_argument('--category', default='Spain2025',
            help='Wiki category (default: %(default)s)')
        parser.add_argument('relations', nargs='*', default=['10492086', '4220975'],
            help='Relation IDs to process [default: %(default)s]')
        args = parser.parse_args()
        if not args.queryName:
            args.queryName="RelationNodesGeo"
        return args


    def query_rel(self, rel: str) -> Dict:
        """
        Query the given relation using SPARQL

        Args:
             rel: The relation ID to query

        Returns:
             Dict: The query results as list of dicts
        """
        if not self.args.queriesPath:
            self.args.queriesPath= self.loc_finder.query_path / "osmplanet.yaml"
        qm = QueryManager(lang='sparql', debug=self.args.debug,
            queriesPath=self.args.queriesPath)
        self.query = qm.queriesByName[self.args.queryName]

        param_dict = {
             'relid': rel,
             'role': self.args.role,
             'min_lat': str(self.args.min_lat),
             'max_lat': str(self.args.max_lat),
             'min_lon': str(self.args.min_lon),
             'max_lon': str(self.args.max_lon)
        }

        if self.args.debug:
            print(f"Querying relation {rel}")

        query_result = self.sparql.queryAsListOfDicts(
             self.query.query, param_dict=param_dict
        )
        if self.args.debug:
            queryString=self.query.query
            params = Params(queryString)
            queryString = params.apply_parameters_with_check(param_dict)
            print(queryString)
        return query_result

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

    def process_relations(self, relations: List[str]):
        """
        Process the given relations

        Args:
             relations: List of relation IDs to process
        """
        for rel in relations:
            json_file = os.path.join(self.tmpdir, f"osm_{rel}.json")
            wiki_file = os.path.join(self.tmpdir, f"{rel}.wiki")

            print(f"Processing relation {rel}")

            # Query and save JSON
            data = self.query_rel(rel)
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)

            # Convert to wiki and save
            wiki = self.to_mediawiki(rel, data)
            with open(wiki_file, 'w') as f:
                f.write(wiki)

            print(f"Created {wiki_file}")


def main():
    """Main entry point"""
    args = OsmRelConverter.get_parser()
    converter = OsmRelConverter(args=args)
    converter.process_relations(args.relations)


if __name__ == "__main__":
    main()
