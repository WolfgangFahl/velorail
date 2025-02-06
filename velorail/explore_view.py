"""
Created on 2025-06-02

@author: wf
"""

from ngwidgets.lod_grid import ListOfDictsGrid, GridConfig
from ngwidgets.webserver import WebSolution
from nicegui import background_tasks, ui

from velorail.explore import Explorer, Node, TriplePos


class ExplorerView:
    """
    SPARQL Explorer nicegui component
    """

    def __init__(
        self,
        solution: WebSolution,
        prefix: str = "osm:relation",
        endpoint_name: str = "osm-qlever",
        summary: bool = False,
    ):
        """
        initialize me with the given solution

        Args:
            solution: the web solution to use
            prefix: the prefix to use
            endpoint_name: name of the endpoint to use
            summary: if True show summary
        """
        self.solution = solution
        self.prefix = prefix
        self.endpoint_name = endpoint_name
        self.summary = summary
        self.explorer = Explorer(endpoint_name)
        self.result_row = None
        self.spinner = None

    def setup_ui(self):
        """
        setup the user interface elements
        """
        self.result_row = ui.row()
        self.spinner = ui.spinner("dots")
        self.spinner.visible = False
        self.lod_grid=None

    def show(self, node_id: str):
        """
        show the exploration for the given node_id

        Args:
            node_id: the id of the node to explore
        """
        self.node_id = node_id
        background_tasks.create(self.update_results())

    def update_lod(self,lod):
        view_lod = []
        for i, record in enumerate(lod):
            view_record = record.copy()
            view_record["#"] = i
            view_lod.append(view_record)
        with self.result_row:
            if self.lod_grid is None:
                self.lod_grid=ListOfDictsGrid(lod)
                self.lod_grid.setup_button_row(["fit","all"])
                self.lod_grid.set_checkbox_selection("#")
            else:
                self.lod_grid.load_lod(view_lod)
                self.lod_grid.update()

    async def update_results(self):
        """
        get and display the exploration results
        """
        try:
            start_node = self.explorer.get_node(self.node_id, self.prefix)
            self.spinner.visible = True
            with self.result_row:
                ui.label(f"Exploring {start_node.qualified_name} on {self.endpoint_name}")
                lod = self.explorer.explore_node(start_node,triple_pos=TriplePos.SUBJECT,summary=self.summary)
                self.result_row.clear()
                if lod:
                    self.update_lod(lod)
        except Exception as ex:
            self.solution.handle_exception(ex)
        finally:
            self.spinner.visible = False
