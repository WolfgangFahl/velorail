"""
Created on 2025-02-01

@author: wf
"""

import os
from pathlib import Path

from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig, WebSolution
from nicegui import Client, app, ui
from velorail.version import Version

class VeloRailWebServer(InputWebserver):
    """WebServer class that manages the server for velorail

    """

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


    def configure_run(self):
        root_path = (
            self.args.root_path
            if self.args.root_path
            else VelorRailWebServer.examples_path()
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


class VeloRailSolution(InputWebSolution):
    """
    the VeloRail solution
    """

    def __init__(self, webserver: VeloRailWebServer, client: Client):
        """
        Initialize the solution

        Calls the constructor of the base solution
        Args:
            webserver (VeloRailWebServer): The webserver instance associated with this context.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)  # Call to the superclass constructor
