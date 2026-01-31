"""
@description: Repository layer for fetching ICE BofA Bonds Indices data from BigQuery.
@author: Rithwik Babu
"""
import logging
from typing import Iterator, List

from google.cloud import bigquery

from hawk_sdk.core.common.utils import get_bigquery_client


class ICEBofABondsIndicesRepository:
    """Repository for accessing ICE BofA Bonds Indices raw data."""

    def __init__(self, environment: str) -> None:
        """Initializes the repository with a BigQuery client.

        :param environment: The environment to fetch data from (e.g., 'production', 'development').
        """
        self.bq_client = get_bigquery_client()
        self.environment = environment

    def fetch_data(
            self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]
    ) -> Iterator[dict]:
        """Fetches raw data from BigQuery for the given date range and hawk_ids using query parameters."""
        total_return_field = f"total_return_{interval}"
        oas_field = f"oas_{interval}"
        duration_modified_field = f"duration_modified_{interval}"
        duration_effective_field = f"duration_effective_{interval}"
        convexity_field = f"convexity_{interval}"

        query = f"""
        WITH records_data AS (
          SELECT 
            r.record_timestamp AS date,
            hi.value AS ticker,
            MAX(CASE WHEN f.field_name = @total_return_field THEN r.double_value END) AS {total_return_field},
            MAX(CASE WHEN f.field_name = @oas_field THEN r.double_value END) AS {oas_field},
            MAX(CASE WHEN f.field_name = @duration_modified_field THEN r.double_value END) AS {duration_modified_field},
            MAX(CASE WHEN f.field_name = @duration_effective_field THEN r.double_value END) AS {duration_effective_field},
            MAX(CASE WHEN f.field_name = @convexity_field THEN r.double_value END) AS {convexity_field}
          FROM 
            `wsb-hc-qasap-ae2e.{self.environment}.records` AS r
          JOIN 
            `wsb-hc-qasap-ae2e.{self.environment}.fields` AS f
            ON r.field_id = f.field_id
          JOIN 
            `wsb-hc-qasap-ae2e.{self.environment}.hawk_identifiers` AS hi
            ON r.hawk_id = hi.hawk_id
          WHERE 
            r.hawk_id IN UNNEST(@hawk_ids)
            AND f.field_name IN (@total_return_field, @oas_field, @duration_modified_field, @duration_effective_field, @convexity_field)
            AND r.record_timestamp BETWEEN @start_date AND @end_date
          GROUP BY 
            date, ticker
        )
        SELECT DISTINCT
          date,
          ticker,
          {total_return_field},
          {oas_field},
          {duration_modified_field},
          {duration_effective_field},
          {convexity_field}
        FROM 
          records_data
        ORDER BY 
          date;
        """

        query_params = [
            bigquery.ArrayQueryParameter("hawk_ids", "INT64", hawk_ids),
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
            bigquery.ScalarQueryParameter("end_date", "STRING", end_date),
            bigquery.ScalarQueryParameter("total_return_field", "STRING", total_return_field),
            bigquery.ScalarQueryParameter("oas_field", "STRING", oas_field),
            bigquery.ScalarQueryParameter("duration_modified_field", "STRING", duration_modified_field),
            bigquery.ScalarQueryParameter("duration_effective_field", "STRING", duration_effective_field),
            bigquery.ScalarQueryParameter("convexity_field", "STRING", convexity_field)
        ]

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            return query_job.result()
        except Exception as e:
            logging.error(f"Failed to fetch data: {e}")
            raise
