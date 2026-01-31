"""
@description: Datasource API for ICE BofA Bonds data access and export functions.
@author: Rithwik Babu
"""
from typing import List

from hawk_sdk.api.ice_bofa_bonds_indices.repository import ICEBofABondsIndicesRepository
from hawk_sdk.api.ice_bofa_bonds_indices.service import ICEBofABondsIndicesService
from hawk_sdk.core.common.data_object import DataObject


class ICEBofABondsIndices:
    """Datasource API for fetching ICE BofA Bond Indices data."""

    def __init__(self, environment="production") -> None:
        """Initializes the ICE BofA Bonds Indices datasource with required configurations."""
        self.repository = ICEBofABondsIndicesRepository(environment=environment)
        self.service = ICEBofABondsIndicesService(self.repository)

    def get_data(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> DataObject:
        """Fetch data for hawk_ids.

        :param start_date: The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :param hawk_ids: A list of specific hawk_ids to filter by.
        :return: A hawk DataObject containing the data.
        """
        return DataObject(
            name="ice_bofa_bonds_index_data",
            data=self.service.get_data(start_date, end_date, interval, hawk_ids)
        )
