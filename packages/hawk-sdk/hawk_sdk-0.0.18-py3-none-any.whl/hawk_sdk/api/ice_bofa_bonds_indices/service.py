"""
@description: Service layer for processing and normalizing Equities data.
@author: Rithwik Babu
"""
from typing import List, Iterator

import pandas as pd

from hawk_sdk.api.ice_bofa_bonds_indices.repository import ICEBofABondsIndicesRepository


class ICEBofABondsIndicesService:
    """Service class for ICE BofA Bonds Indices business logic."""

    def __init__(self, repository: ICEBofABondsIndicesRepository) -> None:
        """Initializes the service with a repository.

        :param repository: An instance of ICEBofABondsIndicesRepository for data access.
        """
        self.repository = repository

    def get_data(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> pd.DataFrame:
        """ICE BofA Bonds Indices and normalizes data into a pandas DataFrame.

        :param start_date: The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A pandas DataFrame containing the normalized data.
        """
        raw_data = self.repository.fetch_data(start_date, end_date, interval, hawk_ids)
        return self._normalize_data(raw_data)

    @staticmethod
    def _normalize_data(data: Iterator[dict]) -> pd.DataFrame:
        """Converts raw data into a normalized pandas DataFrame.

        :param data: An iterator over raw data rows.
        :return: A pandas DataFrame containing normalized data.
        """
        return pd.DataFrame([dict(row) for row in data])
