# AGENTS.md - Development Guide for velorail

CRITICAL: NEVER EVER DO ANY ACTION READING, MODIFYING OR RUNNING without explaining the plan first. Each set of intended actions needs to be explained in the format: I understood that \<YOUR ANALYSIS\> so that i plan to \<GOALS YOU PURSUE\> by \<ACTIONS TO BE CONFIRMED\> confirm with go! YOU WILL NEVER PROCEED WITHOUT POSITIVE CONFIRMATION by go!

## Systematic approach

We are software architects, not hackers. Use the abstractions that are there
before adding new ones. Never read library source code to find out how a tool
works - use it as a user would. Poking around is forbidden.

Every tool execution costs time and money. Knowledge is kept in the wikis - ask
for the information source instead of searching for it.

## Project overview

velorail is multimodal route planning with a focus on bike and train. It is a
NiceGUI/FastAPI web application plus CLI tools. Geodata comes from
OpenStreetMap and Wikidata SPARQL endpoints and from gpx files.

* Demo: https://velorail.bitplan.com
* REST API: https://velorail.bitplan.com/docs
* Wiki: https://wiki.bitplan.com/index.php/Velorail
* API docs: https://WolfgangFahl.github.io/velorail/

## Build/Lint/Test commands

```bash
scripts/install         # pip install .
scripts/test            # unittest discover
scripts/test -g         # green runner
scripts/test -m         # module by module
scripts/test -t         # tox
scripts/blackisort      # isort + black - always before a commit
scripts/doc             # rebuild the mkdocs API documentation
checkos -o WolfgangFahl -p velorail --local -v -ws /Users/wf/py-workspace
```

Single test:

```bash
python -m unittest tests.test_bbox
python -m unittest tests.test_bbox.TestBBox.test_overlap_and_containment
```

Run the server locally:

```bash
python -m velorail.velorail_cmd -s --port 9876
```

## Project structure

```
velorail/                  package
  bbox.py                  BBox - bounding box geometry
  gpx.py                   GpxRoutes - routes and bounding boxes of gpx data
  routefind.py             RouteFinder - OSM route relations by bounding box
  locfind.py               LocFinder - stations, bike nodes, wikidata locations
  npq.py                   NPQ_Handler - named parameterized SPARQL queries
  explore.py               SPARQL graph explorer
  gpxviewer.py             gpx display on a leaflet map
  tour.py                  Tour, Leg, Loc and their styles
  wkt.py                   WKT geometry helpers
  webserver.py             NiceGUI pages and the REST API
  velorail_cmd.py          CLI
  resources/endpoints.yaml SPARQL endpoints
  resources/queries/       named parameterized queries
velorail_examples/         example gpx files - served root of the web server
tests/                     unittest test suite
```

## Named parameterized queries

Queries are never inlined in Python code. They live in
`velorail/resources/queries/*.yaml` with a `param_list` and are run through
`NPQ_Handler.query_by_name`. Endpoints live in
`velorail/resources/endpoints.yaml` and are referenced by name
(`osm-qlever`, `osm-sophox`, `wikidata-qlever`, `wikidata`).

QLever evaluates `geof:sfIntersects` only when both arguments are variables,
so a bounding box polygon is bound with `BIND(...^^geo:wktLiteral AS ?area)`
before it is used in the `FILTER` - see `routes.yaml`.

## REST API

REST routes are registered in `VeloRailWebServer.__init__` with `@app.get` /
`@app.post` and show up automatically in the Swagger UI at `/docs`. Every
handler returns `{"status": "ok", ...}` or `{"status": "error", "message": ...}`
instead of raising - a route that raises is a bug.

## Test conventions

* unittest only - no pytest fixtures, no conftest.py
* test classes derive from `Basetest` of `ngwidgets.basetest`
* files `tests/test_<module>.py`, classes `TestXxx`, methods `test_xxx`
* `self.debug` gates debug output, `Basetest.inPublicCI()` gates tests that
  need network resources which are blocked or unstable on GitHub runners
* tests that need example data use `velorail_examples`, never a remote url

## Code style

* black + isort via `scripts/blackisort`, line length 88
* Google style docstrings, module header with creation date and `@author`
* type hints on all signatures and return types, `Optional[X]` not `X | None`
* one named return variable per function - no expression returns, no multiple
  returns
* top level imports only - optional dependencies via try/except ImportError
* snake_case for new code, camelCase kept where legacy code already uses it
* plain `Exception`, `ValueError`, `RuntimeError` - no own exception hierarchy
* errors never pass silently

## Build system

hatchling only, all configuration in pyproject.toml, version in
`velorail/__init__.py`. The wheel ships `velorail` and `velorail_examples` -
both need an entry in `[tool.hatch.build.targets.wheel.sources]`.

## Ecosystem

* pybasemkit - Basetest, BaseCmd, `@lod_storable`
* pyLoDStorage - LOD, SQLDB, QueryManager, EndpointManager
* ngwidgets - NiceGUI widgets, InputWebserver, LeafletMap
* py-3rdparty-mediawiki - MediaWiki client
* py-ez-wikidata - Wikidata property handling
