"""
Created on 2025-06-02

@author: wf
"""
import re
from ngwidgets.lod_grid import ListOfDictsGrid, GridConfig
from ngwidgets.webserver import WebSolution
from ngwidgets.widgets import Link
from nicegui import background_tasks, ui
from velorail.explore import Explorer, TriplePos

class ExplorerView:
    """SPARQL Explorer nicegui component"""

    def __init__(self, solution: WebSolution, prefix: str = "osm:relation",
                 endpoint_name: str = "osm-qlever", summary: bool = False):
        """Initialize the explorer view"""
        self.solution = solution
        self.prefix = prefix
        self.endpoint_name = endpoint_name
        self.summary = summary
        self.explorer = Explorer(endpoint_name)
        self.result_row = None
        self.lod_grid = None
        self.node_id = None
        self.load_task = None
        self.timeout = 20.0  # seconds
        self.wpm=self.solution.wpm

    def setup_ui(self):
        """Setup the basic UI container"""
        self.header_row=ui.row()
        self.node_info=ui.html(f"Endpoint: {self.endpoint_name}")
        self.result_row = ui.row().classes('w-full')

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
                ui.spinner('dots')
            self.result_row.update()

            # Get exploration results
            start_node = self.explorer.get_node(self.node_id, self.prefix)
            with self.result_row:
                ui.label(f"Exploring {start_node.qualified_name} on {self.endpoint_name}")

            lod = self.explorer.explore_node(
                node=start_node,
                triple_pos=TriplePos.SUBJECT,
                summary=self.summary
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
        for i, record in enumerate(lod):
            view_record = {"#": i + 1}  # Number first
            record_copy = record.copy()
            for key, value in record_copy.items():
                if isinstance(value, str) and value.startswith("http"):
                    if "wikidata" in self.endpoint_name:
                        if "www.wikidata.org/prop" in value:
                            # Get property info if it's a Wikidata property
                            pid = re.sub(r'.*P(\d+).*', r'P\1', value)
                            prop = self.wpm.get_property_by_id(pid)
                            if prop:
                                view_record[key] = Link.create(prop.url, f"{prop.plabel} ({pid})")
                                continue
                    view_record[key] = Link.create(value, value)
                else:
                    view_record[key] = value
            view_lod.append(view_record)
        return view_lod

    def update_lod(self, lod: list):
        """Update grid with list of dicts data"""
        view_lod=self.get_view_lod(lod)
        # Configure grid with checkbox selection
        grid_config = GridConfig(
            key_col="#",
            editable=False,
            multiselect=True,
            with_buttons=True,
            debug=False
        )

        # Create or update grid
        if self.lod_grid is None:
            with self.result_row:
                self.lod_grid = ListOfDictsGrid(lod=view_lod, config=grid_config)
                self.lod_grid.setup_button_row(["fit", "all"])
                self.lod_grid.set_checkbox_selection("#")
        else:
            with self.result_row:
                self.lod_grid.load_lod(view_lod)
                self.lod_grid.update()
                self.lod_grid.sizeColumnsToFit()

    def get_selected_rows(self) -> list:
        """Get the currently selected rows from the grid"""
        if self.lod_grid and self.lod_grid.get_selected_rows():
            return self.lod_grid.get_selected_rows()
        return []