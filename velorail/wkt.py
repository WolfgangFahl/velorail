"""
Created on 2025-02-01

@author: wf
"""

from shapely.geometry import Point
from shapely.wkt import loads


class WKT:
    """
    Utility class for handling WKT (Well Known Text) geometries
    see https://de.wikipedia.org/wiki/Simple_Feature_Access
    """

    @staticmethod
    def wkt_to_latlon(wkt: str):
        """
        Converts a WKT string to (latitude, longitude) for a Point,
        or the centroid for LineString, Polygon, etc.

        params:
          wkt: str - WKT geometry string

        returns:
          tuple(float, float) - (latitude, longitude)
        """
        geom = loads(wkt)
        center = geom if isinstance(geom, Point) else geom.centroid
        return center.y, center.x  # Return as (latitude, longitude)

    @staticmethod
    def wkt_to_latlon_str(wkt: str, precision: int = 5) -> str:
        """
        Convert WKT to lat,lon string
        Args:
            wkt: WKT geometry string
            precision: number of decimal places (default 5 for ~1m precision)
        Returns:
            str: comma separated lat,lon with specified precision
        """
        lat, lon = WKT.wkt_to_latlon(wkt)
        lat_str = f"{lat:.{precision}f}"
        lon_str = f"{lon:.{precision}f}"
        return f"{lat_str},{lon_str}"
