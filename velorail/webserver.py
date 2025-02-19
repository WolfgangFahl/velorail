"""
Created on 2025-02-01

@author: wf
"""

import os
import re

from ez_wikidata.wdproperty import WikidataPropertyManager
from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig
from ngwidgets.widgets import Lang, Link
from nicegui import Client, app, ui

from velorail.explore import Explorer, TriplePos
from velorail.explore_view import ExplorerView
from velorail.gpxviewer import GPXViewer
from velorail.locfind import LocFinder
from velorail.sso_users_solution import SsoSolution
from velorail.version import Version
from velorail.wditem_search import WikidataItemSearch


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
        self.lang = self.args.lang
        self.wpm = self.webserver.wpm
        self.viewer = GPXViewer(args=self.args)

    def configure_menu(self):
        """
        configure my menu
        """
        InputWebSolution.configure_menu(self)
        self.sso_solution = SsoSolution(webserver=self.webserver)
        self.sso_solution.configure_menu()

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

    async def show_wikidata_item(self, qid: str = None):
        """
        show the given wikidata item on the map
        Args:
            qid(str): the Wikidata id of the item to analyze
        """

        def show():
            viewer = self.viewer
            # Create LocFinder and get coordinates
            locfinder = LocFinder()
            center = None
            wd_item = locfinder.get_wikidata_geo(qid)
            if wd_item:
                wd_link = wd_item.as_wd_link()
                wd_maps = wd_item.get_map_links(zoom=self.viewer.zoom)
                # create markup with links
                markup = f"{wd_link}&nbsp;{wd_maps}"
                ui.html(markup)
                center = [wd_item.lat, wd_item.lon]
            viewer.show(center=center)

        await self.setup_content_div(show)

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

    async def show_explorer(
        self,
        node_id: str = None,
        prefix: str = "osm",
        endpoint_name: str = "osm-qlever",
        summary: bool = False,
    ):
        """
        show the SPARQL explorer for the given node

        Args:
            node_id(str): id of the node to explore
            prefix(str): prefix to use e.g. wd:
            endpoint_name(str): name of the endpoint to use
            summary(bool): if True show summary
        """

        def show():
            explorer_view = ExplorerView(
                self, prefix=prefix, endpoint_name=endpoint_name, summary=summary
            )
            explorer_view.setup_ui()
            explorer_view.show(node_id)

        await self.setup_content_div(show)

    def prepare_ui(self):
        """
        overrideable configuration
        """
        self.endpoint_name = self.args.endpointName

    def configure_settings(self):
        """
        configure settings
        """
        lang_dict = Lang.get_language_dict()
        self.add_select("language:", lang_dict).bind_value(self, "lang")

    async def home(self):
        """
        provide the main content page
        """

        def record_filter(qid: str, record: dict):
            """
            filter the given search record
            """
            if "label" and "desc" in record:
                desc = record["desc"]
                label = record["label"]
                text = f"""{label}({qid})☞{desc}"""
                map_link = Link.create(f"/wd/{qid}", text)
                # getting the link to be at second position
                # is a bit tricky
                temp_items = list(record.items())
                # Add the new item in the second position
                temp_items.insert(1, ("map", map_link))

                explore_link = Link.create(
                    f"/explore/{qid}?prefix=wd&endpoint_name=wikidata&summary=True",
                    text,
                )
                temp_items.insert(2, ("explore", explore_link))

                # Clear the original dictionary and update it with the new order of items
                record.clear()
                record.update(temp_items)

        def show():
            self.wd_item_search = WikidataItemSearch(
                self, record_filter=record_filter, lang=self.lang
            )

        await self.setup_content_div(show)


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

        # Initialize property manager instance
        self.wpm = WikidataPropertyManager.get_instance()

        @ui.page("/explore/{node_id}")
        async def explorer_page(
            client: Client,
            node_id: str,
            prefix: str = "osmrel",
            endpoint_name: str = "osm-qlever",
            summary: bool = False,
        ):
            """
            explore the given node id
            """
            await self.page(
                client,
                VeloRailSolution.show_explorer,
                node_id=node_id,
                prefix=prefix,
                endpoint_name=endpoint_name,
                summary=summary,
            )

        @ui.page("/wd/{qid}")
        async def wikidata_item_page(client: Client, qid: str):
            """
            show the given wikidata item on the map
            """
            await self.page(client, VeloRailSolution.show_wikidata_item, qid)

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
                client, VeloRailSolution.show_lines, lines, auth_token, zoom
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
            await self.page(client, VeloRailSolution.show_gpx, gpx, auth_token, zoom)

        @app.get("/api/explore/{node_id}")
        async def explore_api(
            node_id: str,
            prefix: str = "osmrel",
            endpoint_name: str = "osm-qlever",
            summary: bool = False,
        ):
            """
            SPARQL explorer REST API endpoint

            Args:
                node_id: id of the node to explore
                prefix: prefix to use e.g. wd:
                endpoint_name: name of the endpoint to use
                summary: if True show summary

            Returns:
                dict: JSON response with exploration results
            """
            explorer = Explorer(endpoint_name)

            start_node = explorer.get_node(prefix=prefix, node_id=node_id)
            try:
                lod = explorer.explore_node(
                    start_node, triple_pos=TriplePos.SUBJECT, summary=summary
                )
                return {"status": "ok", "records": lod}
            except Exception as ex:
                return {"status": "error", "message": str(ex)}

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
