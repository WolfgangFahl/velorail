"""
Created on 2025-02-01

@author: wf
"""

import sys
from argparse import ArgumentParser

from lodstorage.query import EndpointManager
from ngwidgets.cmd import WebserverCmd

from velorail.gpxviewer import GPXViewer
from velorail.webserver import VeloRailWebServer


class VeloRailCmd(WebserverCmd):
    """
    command line handling for velorail
    """

    def __init__(self):
        """
        constructor
        """
        config = VeloRailWebServer.get_config()
        WebserverCmd.__init__(self, config, VeloRailWebServer)
        pass

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        """
        override the default argparser call
        """
        parser = super().getArgParser(description, version_msg)
        parser.add_argument(
            "-en",
            "--endpointName",
            default="wikidata",
            help=f"Name of the endpoint to use for queries. Available by default: {EndpointManager.getEndpointNames(lang='sparql')}",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="show verbose output [default: %(default)s]",
        )
        parser.add_argument(
            "-rp",
            "--root_path",
            default=VeloRailWebServer.examples_path(),
            help="path to velorail files [default: %(default)s]",
        )
        parser.add_argument("--gpx", required=False, help="URL or path to GPX file")
        parser.add_argument(
            "--token", required=False, help="Authentication token for GPX access"
        )
        parser.add_argument(
            "--zoom",
            type=int,
            default=GPXViewer.default_zoom,
            help="zoom level (default: 11)",
        )
        parser.add_argument(
            "--center",
            nargs=2,
            type=float,
            default=GPXViewer.default_center,
            help="center lat,lon - default: Greenwich",
        )
        return parser


def main(argv: list = None):
    """
    main call
    """
    cmd = VeloRailCmd()
    exit_code = cmd.cmd_main(argv)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
