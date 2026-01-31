"""
@description: Repository layer for fetching Equities data from BigQuery.
@author: Rithwik Babu
"""
import logging
from typing import Iterator, List

from google.cloud import bigquery

from hawk_sdk.core.common.utils import get_bigquery_client


class EquitiesRepository:
    """Repository for accessing Equities raw data."""

    def __init__(self, environment: str) -> None:
        """Initializes the repository with a BigQuery client.

        :param environment: The environment to fetch data from (e.g., 'production', 'development').
        """
        self.bq_client = get_bigquery_client()
        self.environment = environment

    def fetch_adjusted_ohlcv(self, start_date: str, end_date: str, interval: str, hawk_ids: List[int]) -> Iterator[
        dict]:
        """Fetches raw adjusted OHLCV data from BigQuery for the given date range and hawk_ids using query parameters."""
        open_field = f"adjusted_open_{interval}"
        high_field = f"adjusted_high_{interval}"
        low_field = f"adjusted_low_{interval}"
        close_field = f"adjusted_close_{interval}"
        volume_field = f"volume_{interval}"

        query = f"""
        WITH records_data AS (
          SELECT 
            r.record_timestamp AS date,
            hi.value AS ticker,
            MAX(CASE WHEN f.field_name = @open_field THEN r.double_value END) AS {open_field},
            MAX(CASE WHEN f.field_name = @high_field THEN r.double_value END) AS {high_field},
            MAX(CASE WHEN f.field_name = @low_field THEN r.double_value END) AS {low_field},
            MAX(CASE WHEN f.field_name = @close_field THEN r.double_value END) AS {close_field},
            MAX(CASE WHEN f.field_name = @volume_field THEN r.int_value END) AS {volume_field}
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
            AND f.field_name IN (@open_field, @high_field, @low_field, @close_field, @volume_field)
            AND r.record_timestamp BETWEEN @start_date AND @end_date
          GROUP BY 
            date, ticker
        )
        SELECT DISTINCT
          date,
          ticker,
          {open_field},
          {high_field},
          {low_field},
          {close_field},
          {volume_field}
        FROM 
          records_data
        ORDER BY 
          date;
        """

        query_params = [
            bigquery.ArrayQueryParameter("hawk_ids", "INT64", hawk_ids),
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
            bigquery.ScalarQueryParameter("end_date", "STRING", end_date),
            bigquery.ScalarQueryParameter("open_field", "STRING", open_field),
            bigquery.ScalarQueryParameter("high_field", "STRING", high_field),
            bigquery.ScalarQueryParameter("low_field", "STRING", low_field),
            bigquery.ScalarQueryParameter("close_field", "STRING", close_field),
            bigquery.ScalarQueryParameter("volume_field", "STRING", volume_field)
        ]

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            return query_job.result()
        except Exception as e:
            logging.error(f"Failed to fetch OHLC data: {e}")
            raise

    def fetch_adjusted_ohlcv_snapshot(self, timestamp: str, hawk_ids: List[int]) -> Iterator[dict]:
        """Fetches the most recent snapshot data from BigQuery for the given time and hawk_ids."""
        query = f"""
        WITH latest_timestamp AS (
          SELECT
            MAX(r.record_timestamp) AS max_ts
          FROM
            `wsb-hc-qasap-ae2e.{self.environment}.records` AS r
          WHERE
            r.hawk_id IN UNNEST(@hawk_ids)
            AND r.record_timestamp <= @timestamp
        ),
        records_data AS (
          SELECT
            r.record_timestamp AS date,
            hi.value            AS ticker,
            MAX(IF(f.field_name = 'adjusted_open_snapshot',  r.double_value, NULL)) AS adjusted_open_snapshot,
            MAX(IF(f.field_name = 'adjusted_high_snapshot',  r.double_value, NULL)) AS adjusted_high_snapshot,
            MAX(IF(f.field_name = 'adjusted_low_snapshot',   r.double_value, NULL)) AS adjusted_low_snapshot,
            MAX(IF(f.field_name = 'adjusted_close_snapshot', r.double_value, NULL)) AS adjusted_close_snapshot,
            MAX(IF(f.field_name = 'volume_snapshot',         r.int_value,    NULL)) AS volume_snapshot
          FROM
            `wsb-hc-qasap-ae2e.{self.environment}.records`            AS r
          JOIN
            `wsb-hc-qasap-ae2e.{self.environment}.fields`             AS f
              ON r.field_id = f.field_id
          JOIN
            `wsb-hc-qasap-ae2e.{self.environment}.hawk_identifiers`   AS hi
              ON r.hawk_id = hi.hawk_id
          WHERE
            r.hawk_id   IN UNNEST(@hawk_ids)
            AND f.field_name IN (
              'adjusted_open_snapshot', 'adjusted_high_snapshot',
              'adjusted_low_snapshot',  'adjusted_close_snapshot',
              'volume_snapshot'
            )
            AND r.record_timestamp = (SELECT max_ts FROM latest_timestamp)
          GROUP BY
            date, ticker
        )
        SELECT
          date,
          ticker,
          adjusted_open_snapshot,
          adjusted_high_snapshot,
          adjusted_low_snapshot,
          adjusted_close_snapshot,
          volume_snapshot
        FROM
          records_data
        ORDER BY
          ticker;
        """

        query_params = [
            bigquery.ArrayQueryParameter("hawk_ids", "INT64", hawk_ids),
            bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", timestamp)
        ]

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            return query_job.result()
        except Exception as e:
            logging.error(f"Failed to fetch snapshot data: {e}")
            raise
