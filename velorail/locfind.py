"""
Created on 2025-02-01

@author: th
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lodstorage.query import EndpointManager, Query, QueryManager
from lodstorage.sparql import SPARQL
from lodstorage.yamlable import lod_storable
from typing import Optional
from ngwidgets.widgets import Link
from velorail.tour import LegStyles

@lod_storable
class WikidataGeoItem:
    """
    Dataclass for storing Wikidata geographical location data with labels
    """
    qid: str
    lat: float
    lon: float
    label: Optional[str]=None
    description: Optional[str]=None

    def as_wd_link(self)->Link:
        text = f"""{self.label}({self.qid})☞{self.description}"""
        wd_link = Link.create(f"https://www.wikidata.org/wiki/{self.qid}", text)
        return wd_link

    def get_map_links(self, leg_styles:Optional[LegStyles]=None, zoom:int=14) -> str:
        """
        Get HTML markup with icons grouped by map type
        """
        if leg_styles is None:
            leg_styles = LegStyles.default()

        map_links = {
            "openstreetmap.org": ["car", "bus", "plane"],
            "opencyclemap.org": ["bike"],
            "openrailwaymap.org": ["train"],
            "map.openseamap.org": ["ferry"],
            "hiking.waymarkedtrails.org": ["foot"]
        }

        markup = ""
        delim=""
        for map_url, leg_types in map_links.items():
            icons=""
            for leg_type in leg_types:
                leg_style=leg_styles.get_style(leg_type)
                icons+=leg_style.utf8_icon
            tooltip = f"{','.join(leg_types)} map"
            if "car" in leg_types:
                url = f"https://{map_url}/#map={zoom}/{self.lat}/{self.lon}"
            elif "foot" in leg_types:
                url = f"https://{map_url}/#?map={zoom}/{self.lat}/{self.lon}"
            else:
                url = f"https://{map_url}/?zoom={zoom}&lat={self.lat}&lon={self.lon}"
            link=Link.create(url, text=icons, tooltip=tooltip, target="_blank")
            markup+=link+delim
            delim="\n"
        return markup

    @property
    def osm_url(self, map_type:str= "street", zoom: int = 15) -> str:
        """
        Get OpenStreetMap URL for this location

        Args:
            zoom: Zoom level (default=15)

        Returns:
            OpenStreetMap URL for the location
        """
        osm_url=f"https://www.open{map_type}map.org/?mlat={self.lat}&mlon={self.lon}&zoom={zoom}"
        return osm_url

    @classmethod
    def from_record(cls, record: dict) -> 'WikidataGeoItem':
        """
        Create WikidataGeoItem from a dictionary record

        Args:
            record: Dictionary containing lat, lon, label and description

        Returns:
            WikidataGeoRecord instance
        """
        return cls(
            qid=record["qid"],
            lat=float(record["lat"]),
            lon=float(record["lon"]),
            label=record["label"],
            description=record["description"]
        )

class LocFinder:
    """
    Set of methods to lookup different location types
    """

    def __init__(self):
        """
        constructor
        """
        endpoint_path = Path(__file__).parent / "resources" / "endpoints.yaml"
        query_path = Path(__file__).parent / "resources" / "queries" / "locations.yaml"
        if not query_path.is_file():
            raise FileNotFoundError(f"LocFinder queries file not found: {query_path}")
        self.query_manager = QueryManager(
            lang="sparql", queriesPath=query_path.as_posix()
        )
        self.endpoint_manager = EndpointManager.getEndpoints(endpoint_path.as_posix())

    def query(self,query_name:str,param_dict:dict={},endpoint:str="wikidata-qlever"):
        """
        get the result of the given query
        """
        query: Query = self.query_manager.queriesByName.get(query_name)
        sparql_endpoint = self.endpoint_manager[endpoint]
        endpoint = SPARQL(sparql_endpoint.endpoint)
        qres = endpoint.queryAsListOfDicts(query.query,param_dict=param_dict)
        return qres

    def get_wikidata_geo(self, qid: str) -> WikidataGeoItem:
        """
        Get geographical coordinates and metadata for a Wikidata item

        Args:
            qid: Wikidata QID of the item

        Returns:
            WikidataGeoItem with location data and metadata
        """
        lod = self.query(query_name="WikidataGeo", param_dict={"qid": qid})
        if len(lod) >= 1:
            record = lod[0]
            record["qid"] = qid  # Add qid to record for WikidataGeoItem creation
            return WikidataGeoItem.from_record(record)
        return None

    def get_all_train_stations(self):
        lod = self.query(query_name="AllTrainStations")
        return lod


    def get_train_stations_by_coordinates(
        self, latitude: float, longitude: float, radius: float
    ):
        """
        Get all train stations within the given radius around the given latitude and longitude
        """
        lod = self.get_all_train_stations()
        df = pd.DataFrame.from_records(lod)
        # Haversine formula components
        lat1, lon1 = np.radians(latitude), np.radians(longitude)
        lat2, lon2 = np.radians(df["lat"]), np.radians(df["long"])

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of Earth in kilometers

        # Calculate distances
        distances = c * r

        # Add distances to dataframe
        df_with_distances = df.copy()
        df_with_distances["distance_km"] = distances

        # Filter points within radius
        points_within_radius = df_with_distances[
            df_with_distances["distance_km"] <= radius
        ].copy()

        # Sort by distance
        points_within_radius = points_within_radius.sort_values("distance_km")

        return points_within_radius
