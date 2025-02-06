"""
Created on 2025-06-02

@author: wf
"""
from ngwidgets.webserver import WebSolution
from velorail.explore import Explorer, Node, NodeType
from nicegui import ui, background_tasks
from ngwidgets.lod_grid import ListOfDictsGrid

class ExplorerView:
    """
    SPARQL Explorer nicegui component
    """

    def __init__(self, solution: WebSolution,
                 prefix: str="osm:relation",
                 endpoint_name: str="osm-qlever",
                 summary: bool=False):
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
        self.spinner = ui.spinner('dots')
        self.spinner.visible = False

    def show(self, node_id: str):
        """
        show the exploration for the given node_id

        Args:
            node_id: the id of the node to explore
        """
        self.node_id = node_id
        background_tasks.create(self.update_results())

    async def update_results(self):
        """
        get and display the exploration results
        """
        start_node = Node(
            uri=f"{self.prefix}{self.node_id}" if self.prefix else self.node_id,
            value=self.node_id,
            type=NodeType.SUBJECT,
            label=None
        )
        self.spinner.visible = True
        with self.result_row:
            ui.label(f"Exploring {start_node.uri} on {self.endpoint_name}")
            try:
                lod = await background_tasks.create(self.explorer.explore_node(start_node))
                self.result_row.clear()
                if lod:
                    grid = ListOfDictsGrid(lod)
                    grid.show()
            except Exception as ex:
                ui.label(f"Query failed: {str(ex)}")
            finally:
                self.spinner.visible = False