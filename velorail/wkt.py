"""
Created on 2025-02-01

@author: wf
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

from shapely.geometry import LineString, Point, Polygon
from shapely.wkt import loads


@dataclass
class WKT:
    """
    Utility class for handling WKT (Well Known Text) geometries
    """

    wkt: str  # Store WKT string as an instance attribute
    # reference point
    lat: float = None
    lon: float = None

    def to_latlon(self) -> Tuple[float, float]:
        """
        Converts a WKT string to (latitude, longitude) for a Point,
        or the centroid for LineString, Polygon, etc.

        Returns:
            tuple(float, float): (latitude, longitude)
        """
        geom = loads(self.wkt)
        center = geom if isinstance(geom, Point) else geom.centroid
        return center.y, center.x  # (lat, lon)

    def to_latlon_list(self) -> List[Tuple[float, float]]:
        """
        Extracts all (latitude, longitude) coordinate pairs from a WKT geometry.

        Returns:
            list of tuples [(lat, lon), ...] for LineString/Polygon
            or [(lat, lon)] for a Point
        """
        geom = loads(self.wkt)

        if isinstance(geom, Point):
            return [(geom.y, geom.x)]  # Ensure a list for consistency
        elif isinstance(geom, (LineString, Polygon)):
            return [
                (lat, lon) for lon, lat in geom.coords
            ]  # Extract coordinates correctly
        else:
            raise ValueError(f"Unsupported geometry type: {type(geom)}")

    def to_latlon_str(self, precision: int = 5) -> str:
        """
        Convert WKT to a lat,lon string with specified precision.

        Args:
            precision: Number of decimal places (default 5 for ~1m precision)

        Returns:
            str: Comma-separated lat,lon with specified precision
        """
        # if we have no reference point use the centroid
        if not self.lat:
            self.lat, self.lon = self.to_latlon()
        text = f"{self.lat:.{precision}f},{self.lon:.{precision}f}"
        return text

    @staticmethod
    def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on earth using the haversine formula.

        Args:
            lat1: Latitude of first point in degrees
            lon1: Longitude of first point in degrees
            lat2: Latitude of second point in degrees
            lon2: Longitude of second point in degrees

        Returns:
            float: Distance between points in meters
        """
        R = 6371000  # Earth radius in meters
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        a = (
            math.sin(dLat / 2.0) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2.0) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c  # Distance in meters
