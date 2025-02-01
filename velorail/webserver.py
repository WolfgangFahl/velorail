"""
Created on 2025-02-01

@author: wf
"""

import os
import re

from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, ui

from velorail.gpxviewer import GPXViewer
from velorail.version import Version


class VeloRailSolution(InputWebSolution):
    """
    the VeloRail solution
    """

    def __init__(self, webserver: "VeloRailWebServer", client: Client):
        """
        Initialize the solution

        Calls the constructor of the base solution
        Args:
            webserver (VeloRailWebServer): The webserver instance associated with this context.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)  # Call to the superclass constructor
        self.args = self.webserver.args
        self.viewer = GPXViewer(args=self.args)

    def clean_smw_artifacts(self, input_str: str) -> str:
        """
        Remove SMW artifacts ([[SMW::on]] and [[SMW::off]]) from the input string.

        Args:
            input_str (str): Input string containing SMW artifacts.

        Returns:
            str: Cleaned string without SMW markers.
        """
        # Regex to match and remove SMW markers
        return re.sub(r"\[\[SMW::(on|off)\]\]", "", input_str)

    async def show_lines(
        self,
        lines: str = None,
        auth_token: str = None,
        zoom: int = GPXViewer.default_zoom,
    ):
        """
        Endpoint to display routes based on 'lines' parameter.
        """
        if not self.viewer:
            ui.label("Error: Viewer not initialized")
            return

        if self.viewer.args.token and auth_token != self.viewer.args.token:
            ui.label("Error: Invalid authentication token")
            return

        if not lines:
            ui.label("Error: No 'lines' parameter provided")
            return

        # Clean the lines parameter to remove SMW artifacts
        cleaned_lines = self.clean_smw_artifacts(lines)

        # Delegate logic to GPXViewer
        try:
            self.viewer.parse_lines_and_show(cleaned_lines, zoom=zoom)
        except ValueError as e:
            ui.label(f"Error processing lines: {e}")

    async def show_gpx(
        self,
        gpx: str = None,
        auth_token: str = None,
        zoom: int = GPXViewer.default_zoom,
    ):
        """
        GPX viewer page with optional gpx_url and auth_token.
        """
        viewer = self.viewer
        if not viewer:
            ui.label("Error: Viewer not initialized")
            return

        if viewer.args.token and auth_token != viewer.args.token:
            ui.label("Error: Invalid authentication token")
            return

        gpx_to_use = gpx if gpx else viewer.args.gpx
        if gpx_to_use:
            viewer.load_gpx(gpx_to_use)
            viewer.show(zoom=zoom)
        else:
            ui.label(
                "Please provide a GPX file via 'gpx' query parameter or the command line."
            )


class VeloRailWebServer(InputWebserver):
    """WebServer class that manages the server for velorail"""

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2025 velorail team"
        config = WebserverConfig(
            copy_right=copy_right,
            version=Version(),
            default_port=9876,
            short_name="velorail",
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = VeloRailSolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=VeloRailWebServer.get_config())

        @ui.page("/lines")
        async def lines_page(
            client: Client,
            lines: str = None,
            auth_token: str = None,
            zoom: int = GPXViewer.default_zoom,
        ):
            """
            Endpoint to display routes based on 'lines' parameter.
            """
            await self.page(
                client, VeloRailSolution.show_lines,lines, auth_token, zoom
            )

        @ui.page("/gpx")
        async def gpx_page(
            client: Client,
            gpx: str = None,
            auth_token: str = None,
            zoom: int = GPXViewer.default_zoom,
        ):
            """
            GPX viewer page with optional gpx_url and auth_token.
            """
            await self.page(client, VeloRailSolution.show_gpx,gpx, auth_token, zoom)

    def configure_run(self):
        root_path = (
            self.args.root_path
            if self.args.root_path
            else VeloRailWebServer.examples_path()
        )
        self.root_path = os.path.abspath(root_path)
        self.allowed_urls = [
            "https://raw.githubusercontent.com/WolfgangFahl/velorail/main/velorail_examples/",
            self.examples_path(),
            self.root_path,
        ]

    @classmethod
    def examples_path(cls) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../velorail_examples")
        path = os.path.abspath(path)
        return path
