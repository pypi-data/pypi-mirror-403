"""
@description: Datasource API for Universal data access and export functions.
@author: Rithwik Babu
"""
from typing import List

from hawk_sdk.api.universal.repository import UniversalRepository
from hawk_sdk.api.universal.service import UniversalService
from hawk_sdk.core.common.data_object import DataObject


class Universal:
    """Datasource API for fetching any data via hawk_ids and field_ids."""

    def __init__(self, environment="production") -> None:
        """Initializes the Universal datasource with required configurations."""
        self.repository = UniversalRepository(environment=environment)
        self.service = UniversalService(self.repository)

    def get_data(
        self,
        hawk_ids: List[int],
        field_ids: List[int],
        start_date: str,
        end_date: str,
        interval: str
    ) -> DataObject:
        """Fetch data for any combination of hawk_ids and field_ids.

        Returns a DataFrame with columns: date, hawk_id, ticker, and one column
        per field. If a hawk_id doesn't have a value for a field on a given date,
        the value will be empty (NaN).

        :param hawk_ids: A list of hawk_ids to fetch data for.
        :param field_ids: A list of field_ids to fetch data for.
        :param start_date: The start date for the data query (YYYY-MM-DD).
        :param end_date: The end date for the data query (YYYY-MM-DD).
        :param interval: The interval for the data query (e.g., '1d', '1h', '1m').
        :return: A hawk DataObject containing the data.
        """
        return DataObject(
            name="universal_data",
            data=self.service.get_data(hawk_ids, field_ids, start_date, end_date, interval)
        )

    def get_field_ids(self, field_names: List[str]) -> DataObject:
        """Lookup field_ids for the given field names.

        Useful for discovering field_ids when you know the field names.

        :param field_names: A list of field name strings to lookup.
        :return: A hawk DataObject containing field_id and field_name pairs.
        """
        return DataObject(
            name="field_ids",
            data=self.service.get_field_ids(field_names)
        )

    def get_all_fields(self) -> DataObject:
        """Get all available fields in the system.

        Useful for discovering available field_ids and their names.

        :return: A hawk DataObject containing all field_id and field_name pairs.
        """
        return DataObject(
            name="all_fields",
            data=self.service.get_all_fields()
        )
