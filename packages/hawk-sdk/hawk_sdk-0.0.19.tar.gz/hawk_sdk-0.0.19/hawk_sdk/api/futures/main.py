"""
@description: Datasource API for Hawk Global Futures data access and export functions.
@author: Rithwik Babu
"""
from typing import List

from hawk_sdk.api.futures.repository import FuturesRepository
from hawk_sdk.api.futures.service import FuturesService
from hawk_sdk.core.common.data_object import DataObject


class Futures:
    """Datasource API for fetching Futures data."""

    def __init__(self, environment="production") -> None:
        """Initializes the Futures datasource with required configurations."""
        self.repository = FuturesRepository(environment=environment)
        self.service = FuturesService(self.repository)

    def get_ohlcvo(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> DataObject:
        """Fetch open, high, low, close, volume, and open interest data for the given date range and hawk_ids.

        :param start_date:    %The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A hawk DataObject containing the data.
        """
        return DataObject(
            name="futures_ohlcvo",
            data=self.service.get_ohlcvo(start_date, end_date, interval, hawk_ids)
        )
