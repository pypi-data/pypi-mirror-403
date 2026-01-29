"""Tick data transformation module for yfinance data.

Provides transformation operations specific to financial tick data extracted
from yfinance sources, including data cleaning and temporal partitioning.
"""

import logging
from attrs import define

from mynk_etl.transform.transform import Transform
from mynk_etl.sparkUtils.sparkComfunc import colTrim, dateTimePartition
from mynk_etl.utils.common.constants import Constants

from pyspark.sql import DataFrame


logger = logging.getLogger(__name__)

@define(slots=True)
class TickTransform(Transform):
    """Transform financial tick data from yfinance sources.

    Applies data cleaning (whitespace trimming) and temporal partitioning
    to financial tick data for optimized storage and querying.
    """
    
    def transformTickData(self) -> DataFrame:
        """Transform tick data by cleaning and adding temporal partitions.

        Performs the following transformations:
        1. Trims whitespace from all string columns
        2. Adds year, month, day partition columns based on record timestamp
        3. Converts timestamp to TimestampNTZType for Iceberg compatibility

        Returns:
            DataFrame: Transformed DataFrame with cleaned data and partition columns
        """

        self.df = colTrim(self.df)
        # self.df = self.df.withColumn(Constants.RECORD_TIMESTAMP_KEY.value, from_utc_timestamp(to_timestamp("utc_str"), "Asia/Kolkata"))
        logger.debug("Trimmed whitespace from string columns.")
        self.df = dateTimePartition(self.df, Constants.RECORD_TIMESTAMP_KEY.value)
        logger.debug("Added year, month, day partitions based on 'timestamp' column.")

        return self.df