"""
Created on 2024-01-03

@author: wf
"""

import asyncio
from typing import Callable

from ez_wikidata.wdsearch import WikidataSearch
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.webserver import WebSolution
from ngwidgets.widgets import Link
from nicegui import ui


class WikidataItemSearch:
    """
    wikidata item search
    """

    def __init__(
        self, solution: WebSolution, record_filter: Callable = None, lang: str = "en"
    ):
        """
        Initialize the WikidataItemSearch with the given solution.

        Args:
            solution (WebSolution): The solution to attach the search UI.
            record_filter(Callable): callback for displayed found records
        """
        self.solution = solution
        self.lang = lang
        self.record_filter = record_filter
        self.limit = 9
        self.wd_search = WikidataSearch(lang)
        self.search_debounce_task = None
        self.keyStrokeTime = 0.65  # minimum time in seconds to wait between keystrokes before starting searching
        self.search_result_row = None
        self.setup()

    def setup(self):
        """
        setup the user interface
        """
        with ui.card().style("width: 25%"):
            with ui.grid(rows=1, columns=4):
                ui.label("limit:")
                self.limit_slider = (
                    ui.slider(min=2, max=50, value=self.limit)
                    .props("label-always")
                    .bind_value(self, "limit")
                )
            with ui.row():
                self.search_input = ui.input(
                    label="search", on_change=self.on_search_change
                ).props("size=80")
        with ui.row() as self.search_result_row:
            self.search_result_grid = ListOfDictsGrid()

    async def on_search_change(self, _args):
        """
        react on changes in the search input
        """
        # Cancel the existing search task if it's still waiting
        if self.search_debounce_task:
            self.search_debounce_task.cancel()

        # Create a new task for the new search
        self.search_debounce_task = asyncio.create_task(self.debounced_search())

    async def debounced_search(self):
        """
        Waits for a period of inactivity and then performs the search.
        """
        try:
            # Wait for the debounce period (keyStrokeTime)
            await asyncio.sleep(self.keyStrokeTime)
            search_for = self.search_input.value
            if self.search_result_row:
                with self.search_result_row:
                    lang = self.lang
                    ui.notify(f"searching wikidata for {search_for} ({lang})...")
                    self.wd_search.language = lang
                    wd_search_result = self.wd_search.searchOptions(
                        search_for, limit=self.limit
                    )
                    view_lod = self.get_selection_view_lod(wd_search_result)
                    self.search_result_grid.load_lod(view_lod)
                    # self.search_result_grid.set_checkbox_selection("#")
                    self.search_result_grid.update()
        except asyncio.CancelledError:
            # The search was cancelled because of new input, so just quietly exit
            pass
        except BaseException as ex:
            self.solution.handle_exception(ex)

    def get_selection_view_lod(self, wd_search_result: list) -> dict:
        """
        Convert the Wikidata search result list of dict to a selection.

        Args:
            wd_search_result (List[Dict[str, Any]]): The search results from Wikidata.

        Returns:
            List[Dict[str, Any]]: The list of dictionaries formatted for view.
        """
        view_lod = []
        for qid, itemLabel, desc in wd_search_result:
            url = f"https://www.wikidata.org/wiki/{qid}"
            link = Link.create(url, qid)
            row = {
                "#": len(view_lod) + 1,
                "qid": link,
                "label": itemLabel,
                "desc": desc,
            }
            if self.record_filter:
                self.record_filter(qid, row)
            view_lod.append(row)
        return view_lod
