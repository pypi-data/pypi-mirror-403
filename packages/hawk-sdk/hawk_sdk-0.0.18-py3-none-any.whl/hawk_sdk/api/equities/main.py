"""
@description: Datasource API for Equities data access and export functions.
@author: Rithwik Babu
"""
from typing import List

from hawk_sdk.api.equities.repository import EquitiesRepository
from hawk_sdk.api.equities.service import EquitiesService
from hawk_sdk.core.common.data_object import DataObject


class Equities:
    """Datasource API for fetching Futures data."""

    def __init__(self, environment="production") -> None:
        """Initializes the Equities datasource with required configurations."""
        self.repository = EquitiesRepository(environment=environment)
        self.service = EquitiesService(self.repository)

    def get_adjusted_ohlcv(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> DataObject:
        """Fetch open, high, low, close data for the given date range and hawk_ids.

        :param start_date: The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A hawk DataObject containing the data.
        """
        return DataObject(
            name="adjusted_equities_ohlcv",
            data=self.service.get_adjusted_ohlcv(start_date, end_date, interval, hawk_ids)
        )

    def get_adjusted_ohlcv_snapshot(self, timestamp: str, hawk_ids: List[int]) -> DataObject:
        """Fetch snapshot data for the given date and hawk_ids.

        :param timestamp: The timestamp for the data query (YYYY-MM-DD HH:MM:SS).
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A hawk DataObject containing the data.
        """
        return DataObject(
            name="equities_adjusted_ohlcv_snapshot",
            data=self.service.get_adjusted_ohlcv_snapshot(timestamp, hawk_ids)
        )
