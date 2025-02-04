"""
Created on 2025-02-01

@author: th
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lodstorage.query import EndpointManager, Query, QueryManager
from lodstorage.sparql import SPARQL
from lodstorage.params import Params

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
