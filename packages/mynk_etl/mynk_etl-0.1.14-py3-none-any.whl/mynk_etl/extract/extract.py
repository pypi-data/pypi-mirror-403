"""Abstract base class for data extraction operations.

This module defines the Extract abstract base class that serves as an interface
for implementing various data extraction strategies (e.g., Kafka, databases).
"""

from attrs import define, field, validators
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame, SparkSession

@define(kw_only=True)
class Extract(ABC):
    """Abstract base class for data extraction.

    Provides interface for extracting data using PySpark in both streaming
    and batch modes from various sources.

    Attributes:
        spark (SparkSession): PySpark session for data operations
        key (str): Configuration key for identifying extraction parameters
    """
    spark: SparkSession = field(validator=validators.instance_of(SparkSession))
    key: str = field(eq=str)

    @abstractmethod
    def extractSparkStreamData(self, topic: str) -> DataFrame:
        """Extract data in streaming mode.

        Args:
            topic (str): Topic or source identifier for streaming data extraction

        Returns:
            DataFrame: Streaming DataFrame with extracted data
        """
        ...

    @abstractmethod
    def extractSparkData(self, topic: str) -> DataFrame:
        """Extract data in batch mode.

        Args:
            topic (str): Topic or source identifier for batch data extraction

        Returns:
            DataFrame: Batch DataFrame with extracted data
        """
        ...