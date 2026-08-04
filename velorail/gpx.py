"""
Created on 2026-08-04

@author: wf

Bounding box view on gpx data see
https://github.com/WolfgangFahl/velorail/issues/5
"""

from dataclasses import field
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import gpxpy
import requests
from basemkit.yamlable import lod_storable

from velorail.bbox import BBox


@lod_storable
class GpxRoute:
    """
    A single named route of a gpx file with its bounding box
    """

    name: str
    kind: str  # "track", "route" or "waypoints"
    point_count: int
    bbox: BBox


@lod_storable
class GpxRoutes:
    """
    The routes of a gpx file
    """

    source: str
    routes: List[GpxRoute] = field(default_factory=list)

    def routes_in_bbox(self, bbox: BBox, mode: str = "overlap") -> List[GpxRoute]:
        """
        Get my routes that match the given target bounding box.

        Args:
            bbox: the target bounding box
            mode: "overlap" or "contained"

        Returns:
            list: the matching GpxRoute entries
        """
        matching = []
        for route in self.routes:
            if route.bbox.matches(bbox, mode=mode):
                matching.append(route)
        return matching

    @classmethod
    def of_gpx(cls, gpx: gpxpy.gpx.GPX, source: str) -> "GpxRoutes":
        """
        Get the routes of the given parsed gpx data.

        Args:
            gpx: the parsed gpx data
            source: the origin of the gpx data e.g. a url

        Returns:
            GpxRoutes: the routes with their bounding boxes
        """
        routes = []
        for index, track in enumerate(gpx.tracks):
            latlons = []
            for segment in track.segments:
                latlons.extend(cls.latlons_of(segment.points))
            route = cls.route_of(track.name, "track", index, latlons)
            if route:
                routes.append(route)
        for index, gpx_route in enumerate(gpx.routes):
            latlons = cls.latlons_of(gpx_route.points)
            route = cls.route_of(gpx_route.name, "route", index, latlons)
            if route:
                routes.append(route)
        if gpx.waypoints:
            latlons = cls.latlons_of(gpx.waypoints)
            route = cls.route_of(gpx.name, "waypoints", 0, latlons)
            if route:
                routes.append(route)
        gpx_routes = cls(source=source, routes=routes)
        return gpx_routes

    @classmethod
    def of_text(cls, gpx_text: str, source: str = "posted") -> "GpxRoutes":
        """
        Get the routes of the given gpx markup.

        Args:
            gpx_text: the gpx xml markup
            source: the origin of the gpx data

        Returns:
            GpxRoutes: the routes with their bounding boxes

        Raises:
            ValueError: if the markup can not be parsed
        """
        try:
            gpx = gpxpy.parse(gpx_text)
        except gpxpy.gpx.GPXXMLSyntaxException as ex:
            raise ValueError(f"invalid gpx markup from {source}: {ex}")
        gpx_routes = cls.of_gpx(gpx, source)
        return gpx_routes

    @classmethod
    def of_url(cls, gpx_url: str, timeout: float = 10.0) -> "GpxRoutes":
        """
        Get the routes of the gpx file at the given url.

        Args:
            gpx_url: the url of the gpx file
            timeout: the request timeout in seconds

        Returns:
            GpxRoutes: the routes with their bounding boxes

        Raises:
            ValueError: if the url scheme is not http or https or the gpx is invalid
            RuntimeError: if the gpx file can not be fetched
        """
        scheme = urlparse(gpx_url).scheme
        if scheme not in ("http", "https"):
            raise ValueError(f"invalid gpx url scheme {scheme} - use http or https")
        try:
            response = requests.get(gpx_url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as ex:
            raise RuntimeError(f"failed to load gpx from {gpx_url}: {ex}")
        gpx_text = cls.text_of_response(response, gpx_url)
        gpx_routes = cls.of_text(gpx_text, source=gpx_url)
        return gpx_routes

    @classmethod
    def text_of_response(cls, response: requests.Response, source: str) -> str:
        """
        Get the gpx markup of the given http response.

        A login protected source answers with an html page and http status 200
        which would otherwise show up as a misleading xml syntax error.

        Args:
            response: the http response to check
            source: the url the response came from

        Returns:
            str: the gpx markup

        Raises:
            ValueError: if the response carries html instead of gpx markup
        """
        gpx_text = response.text
        content_type = response.headers.get("content-type", "").lower()
        is_html = "html" in content_type
        is_html = is_html or gpx_text.lstrip()[:14].lower() == "<!doctype html"
        if is_html:
            raise ValueError(
                f"{source} delivered html and not gpx - a login might be required"
            )
        return gpx_text

    @classmethod
    def latlons_of(cls, points: list) -> List[Tuple[float, float]]:
        """
        Get the (latitude, longitude) pairs of the given gpx points.

        Args:
            points: the gpx points to convert

        Returns:
            list: the list of (latitude, longitude) tuples
        """
        latlons = []
        for point in points:
            if point.latitude is not None and point.longitude is not None:
                latlons.append((point.latitude, point.longitude))
        return latlons

    @classmethod
    def route_of(
        cls,
        name: Optional[str],
        kind: str,
        index: int,
        latlons: List[Tuple[float, float]],
    ) -> Optional[GpxRoute]:
        """
        Get the GpxRoute for the given points.

        Args:
            name: the name of the track or route if any
            kind: "track", "route" or "waypoints"
            index: the position of the track or route in the gpx file
            latlons: the (latitude, longitude) pairs of the route

        Returns:
            GpxRoute: the route or None if there are no points
        """
        route = None
        bbox = BBox.of_latlons(latlons)
        if bbox:
            route_name = name if name else f"{kind} {index + 1}"
            route = GpxRoute(
                name=route_name,
                kind=kind,
                point_count=len(latlons),
                bbox=bbox,
            )
        return route
