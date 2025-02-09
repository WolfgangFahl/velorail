"""
Created on 2025-06-02

@author: wf
"""

import re

from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.webserver import WebSolution
from ngwidgets.widgets import Link
from nicegui import background_tasks, ui

from velorail.explore import Explorer, TriplePos
from velorail.querygen import QueryGen


class ExplorerView:
    """SPARQL Explorer nicegui component"""

    def __init__(
        self,
        solution: WebSolution,
        prefix: str = "osm:relation",
        endpoint_name: str = "osm-qlever",
        summary: bool = False,
    ):
        """Initialize the explorer view"""
        self.solution = solution
        self.args = self.solution.args
        self.prefix = prefix
        self.endpoint_name = endpoint_name
        self.summary = summary
        self.explorer = Explorer(endpoint_name)
        self.result_row = None
        self.lod_grid = None
        self.node_id = None
        self.load_task = None
        self.timeout = 20.0  # seconds
        self.wpm = self.solution.wpm

    async def get_selected_lod(self):
        """
        selected rows are in view (e.g.  html) format
        get back the original list of dict rows
        """
        lod = []
        selected_rows = await self.lod_grid.get_selected_rows()
        if not selected_rows:
            with self.result_row:
                ui.notify("Please select at least one row")
        else:
            for row in selected_rows:
                index = row["#"]
                record = self.dod[index]
                lod.append(record)
        return lod

    async def on_generate_query(self):
        """Handle query generation from selected rows"""
        try:
            lod = await self.get_selected_lod()
            prefixes = self.explorer.endpoint_prefixes.get(self.endpoint_name)
            query_gen = QueryGen(prefixes, debug=self.args.debug)
            sparql_query = query_gen.gen(
                lod,
                main_var="item",
                main_value=f"{self.prefix}:{self.node_id}"
            )
            self.query_code.content = sparql_query
        except Exception as ex:
            self.solution.handle_exception(ex)

    async def on_run_query(self):
        """
        Run the given SPARQL query and display the result.
        """
        try:
            if not self.query_code.content.strip():
                with self.result_row:
                    ui.notify("No query generated. Please generate a query first.")
                return

            sparql_query = self.query_code.content.strip()

            # Execute the query
            lod = self.explorer.query(
                sparql_query=sparql_query,
                param_dict={},
                endpoint=self.endpoint_name
            )

            # Ensure only one record is expected
            if not lod:
                with self.result_row:
                    ui.notify("Query returned no results.")
                return

            if len(lod) > 1:
                with self.result_row:
                    ui.notify("Unexpected multiple results. Displaying first result only.")

            # Transform result into a single-row format for display
            record = lod[0]  # Expecting a single record
            single_record_lod = [{"Property": key, "Value": value} for key, value in record.items()]
            self.update_lod(single_record_lod, with_select=False)

        except Exception as ex:
            self.solution.handle_exception(ex)

    def get_default_query(self) -> str:
        """ """
        if self.node_id is None:
            node_id = "10492086"
        else:
            node_id = self.node_id
        query = (
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX osm2rdfmember: <https://osm2rdf.cs.uni-freiburg.de/rdf/member#>
PREFIX osmrel: <https://www.openstreetmap.org/relation/>
PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
SELECT
  ?rel
  ?rel_name
  ?rel_pos
  ?member
  ?node
  ?node_name
  ?node_ref
  ?role
  ?lat
  ?lon
WHERE {
  VALUES (?rel ?role ?minlat ?maxlat ?minlon ?maxlon) {
    (osmrel:"""
            + node_id
            + """ "stop" 42.0 44.0 -9.0 4.0)
  }
  ?rel osmkey:ref ?rel_name .
#  ?rel osmrel:member_ref ?member .
#  ?member osmrel:member_pos ?rel_pos .
#  ?member osmrel:member_role ?role .
#  ?member osmrel:member_id ?node .
#  OPTIONAL { ?node osmkey:name ?node_name}.
#  OPTIONAL { ?node osmkey:ref ?node_ref}.
#  ?node geo:hasGeometry/geo:asWKT ?loc .
#  BIND(geof:latitude(?loc) AS ?lat)
#  BIND(geof:longitude(?loc) AS ?lon)
#  FILTER (?lat > ?minlat && ?lat < ?maxlat && ?lon > ?minlon && ?lon < ?maxlon)
}
#ORDER BY ?rel_pos
"""
        )
        return query

    def setup_ui(self):
        """Setup the basic UI container"""
        with ui.splitter() as splitter:
            with splitter.before:
                self.header_row = ui.row()
                with self.header_row:
                    self.node_info = ui.html(
                        f"{self.prefix}:{self.node_id} Endpoint: {self.endpoint_name}"
                    )
                    ui.button(
                        "Generate Query", icon="code", on_click=self.on_generate_query
                    )
                    self.result_row = ui.row().classes("w-full")
            with splitter.after:
                ui.button("run", icon="code", on_click=self.on_run_query)
                self.query_code = (
                    ui.code(content=self.get_default_query(), language="SPARQL")
                    .classes("w-full")
                    .props("rows=10")
                )

    def show(self, node_id: str):
        """Show exploration results for a given node ID"""
        self.node_id = node_id
        self.run_exploration()

    async def explore_node_task(self):
        """Background task for node exploration"""
        try:
            # Clear and show loading state
            self.result_row.clear()
            with self.result_row:
                ui.spinner("dots")
            self.result_row.update()

            # Get exploration results
            start_node = self.explorer.get_node(self.node_id, self.prefix)
            with self.result_row:
                ui.label(
                    f"Exploring {start_node.qualified_name} on {self.endpoint_name}"
                )

            lod = self.explorer.explore_node(
                node=start_node, triple_pos=TriplePos.SUBJECT, summary=self.summary
            )

            if not lod:
                with self.solution.container:
                    ui.notify("Exploration returned no results")
                return

            self.result_row.clear()
            self.update_lod(lod)

        except Exception as ex:
            self.solution.handle_exception(ex)
            with self.solution.container:
                ui.notify(f"Exploration failed: {str(ex)}")

    def run_exploration(self):
        """Run the exploration with proper task management"""

        def cancel_running():
            if self.load_task:
                self.load_task.cancel()

        # Cancel any running task
        cancel_running()

        # Set timeout
        ui.timer(self.timeout, lambda: cancel_running(), once=True)

        # Run new task in background
        self.load_task = background_tasks.create(self.explore_node_task())

    def get_view_lod(self, lod: list) -> list:
        """Convert records to view format with row numbers and links"""
        view_lod = []
        self.dod = {}
        for i, record in enumerate(lod):
            index = i + 1
            view_record = {"#": index}  # Number first
            # dict of dicts for lookup by index
            self.dod[index] = record
            record_copy = record.copy()
            for key, value in record_copy.items():
                if isinstance(value, str) and value.startswith("http"):
                    if "wikidata" in self.endpoint_name:
                        if "www.wikidata.org/prop" in value:
                            # Get property info if it's a Wikidata property
                            pid = re.sub(r".*P(\d+).*", r"P\1", value)
                            prop = self.wpm.get_property_by_id(pid)
                            if prop:
                                view_record[key] = Link.create(
                                    prop.url, f"{prop.plabel} ({pid})"
                                )
                                continue
                    view_record[key] = Link.create(value, value)
                else:
                    view_record[key] = value
            view_lod.append(view_record)
        return view_lod

    def update_lod(self, lod: list,with_select:bool=True):
        """Update grid with list of dicts data"""
        view_lod = self.get_view_lod(lod)
        # Configure grid with checkbox selection
        grid_config = GridConfig(
            key_col="#",
            editable=False,
            multiselect=True,
            with_buttons=True,
            debug=False,
        )

        # Create or update grid
        if self.lod_grid is None:
            with self.result_row:
                self.lod_grid = ListOfDictsGrid(lod=view_lod, config=grid_config)
                self.lod_grid.setup_button_row(["fit", "all"])
        else:
            with self.result_row:
                self.lod_grid.load_lod(view_lod)
                self.lod_grid.update()
                self.lod_grid.sizeColumnsToFit()
        with self.result_row:
            if with_select:
                self.lod_grid.set_checkbox_selection("#")
