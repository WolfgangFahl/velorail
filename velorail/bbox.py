"""
Created on 2026-08-04

@author: wf

Bounding box handling for route lookups see
https://github.com/WolfgangFahl/velorail/issues/5
"""

from typing import List, Optional, Tuple

from basemkit.yamlable import lod_storable
from shapely.geometry import box


@lod_storable
class BBox:
    """
    A geographic bounding box in WGS84 degrees
    """

    south: float
    west: float
    north: float
    east: float

    def __post_init__(self):
        """
        Check the bounds.

        Raises:
            ValueError: if a bound is out of range or the box is inverted
        """
        self.south = float(self.south)
        self.west = float(self.west)
        self.north = float(self.north)
        self.east = float(self.east)
        for name, lat in [("south", self.south), ("north", self.north)]:
            if not -90.0 <= lat <= 90.0:
                raise ValueError(f"{name} latitude {lat} is out of range -90..90")
        for name, lon in [("west", self.west), ("east", self.east)]:
            if not -180.0 <= lon <= 180.0:
                raise ValueError(f"{name} longitude {lon} is out of range -180..180")
        if self.south > self.north:
            raise ValueError(f"south {self.south} is north of north {self.north}")
        if self.west > self.east:
            raise ValueError(f"west {self.west} is east of east {self.east}")

    @property
    def polygon(self):
        """
        Get the shapely polygon for this bounding box.

        Returns:
            Polygon: the box in lon lat order
        """
        polygon = box(self.west, self.south, self.east, self.north)
        return polygon

    @property
    def center(self) -> Tuple[float, float]:
        """
        Get the center of this bounding box.

        Returns:
            tuple(float, float): (latitude, longitude) of the center
        """
        center = (
            (self.south + self.north) / 2.0,
            (self.west + self.east) / 2.0,
        )
        return center

    def as_wkt(self) -> str:
        """
        Get the WKT polygon representation in lon lat order.

        Returns:
            str: the WKT POLYGON markup
        """
        wkt = self.polygon.wkt
        return wkt

    def as_param_dict(self, limit: Optional[int] = None) -> dict:
        """
        Get the parameter dict for the named parameterized bounds queries.

        Args:
            limit: the optional result limit to add

        Returns:
            dict: the south/west/north/east parameters
        """
        param_dict = {
            "south": self.south,
            "west": self.west,
            "north": self.north,
            "east": self.east,
        }
        if limit is not None:
            param_dict["limit"] = limit
        return param_dict

    def overlaps(self, other: "BBox") -> bool:
        """
        Check whether this bounding box overlaps the other one.

        Args:
            other: the bounding box to check against

        Returns:
            bool: True if the boxes share at least one point
        """
        overlaps = self.polygon.intersects(other.polygon)
        return overlaps

    def is_within(self, other: "BBox") -> bool:
        """
        Check whether this bounding box is contained in the other one.

        Args:
            other: the bounding box to check against

        Returns:
            bool: True if this box lies completely within the other box
        """
        is_within = other.polygon.covers(self.polygon)
        return is_within

    def matches(self, other: "BBox", mode: str = "overlap") -> bool:
        """
        Check this bounding box against the other one in the given mode.

        Args:
            other: the target bounding box
            mode: "overlap" or "contained"

        Returns:
            bool: True if this box matches the target box

        Raises:
            ValueError: if the mode is unknown
        """
        if mode == "overlap":
            matches = self.overlaps(other)
        elif mode == "contained":
            matches = self.is_within(other)
        else:
            raise ValueError(f"invalid mode {mode} - use overlap or contained")
        return matches

    @classmethod
    def of_latlons(cls, latlons: List[Tuple[float, float]]) -> Optional["BBox"]:
        """
        Get the bounding box of the given (latitude, longitude) pairs.

        Args:
            latlons: the list of (latitude, longitude) tuples

        Returns:
            BBox: the enclosing bounding box or None if there are no points
        """
        bbox = None
        if latlons:
            lats = [latlon[0] for latlon in latlons]
            lons = [latlon[1] for latlon in latlons]
            bbox = cls(south=min(lats), west=min(lons), north=max(lats), east=max(lons))
        return bbox
