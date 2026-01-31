"""
@description: Service layer for processing and normalizing Futures data.
@author: Rithwik Babu
"""
from typing import List, Iterator

import pandas as pd

from hawk_sdk.api.futures.repository import FuturesRepository


class FuturesService:
    """Service class for Futures business logic."""

    def __init__(self, repository: FuturesRepository) -> None:
        """Initializes the service with a repository.

        :param repository: An instance of FuturesRepository for data access.
        """
        self.repository = repository

    def get_ohlcvo(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> pd.DataFrame:
        """Fetches and normalizes data into a pandas DataFrame.

        :param start_date: The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A pandas DataFrame containing the normalized data.
        """
        raw_data = self.repository.fetch_ohlcvo(start_date, end_date, interval, hawk_ids)
        return self._normalize_data(raw_data)

    @staticmethod
    def _normalize_data(data: Iterator[dict]) -> pd.DataFrame:
        """Converts raw data into a normalized pandas DataFrame.

        :param data: An iterator over raw data rows.
        :return: A pandas DataFrame containing normalized data.
        """
        return pd.DataFrame([dict(row) for row in data])
