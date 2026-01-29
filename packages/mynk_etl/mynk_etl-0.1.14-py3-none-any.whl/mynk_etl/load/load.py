"""Abstract base class for data loading operations.

This module defines the Load abstract base class that serves as an interface
for implementing various data writing/loading strategies (e.g., Iceberg, RDBMS, files).
"""

from attrs import define, field, validators
from abc import ABC, abstractmethod
from typing import Any

from pyspark.sql import DataFrame, SparkSession

@define(kw_only=True)
class Load(ABC):
    """Abstract base class for data loading/writing.

    Provides interface for writing/loading data using PySpark in both streaming
    and batch modes to various destinations.

    Attributes:
        spark (SparkSession): PySpark session for data operations
        df (DataFrame): DataFrame to be written/loaded
        key (str): Configuration key for identifying loading parameters
    """
    spark: SparkSession = field(validator=validators.instance_of(SparkSession))
    df: DataFrame = field(validator=validators.instance_of(DataFrame))
    key: str = field(eq=str)

    @abstractmethod
    def streamWriter(self, param_dct: dict[str, Any]) -> None:
        """Write data in streaming mode.

        Args:
            param_dct (dict[str, Any]): Dictionary containing streaming write parameters
        """
        ...

    @abstractmethod
    def nonStreamWriter(self, param_dct: dict[str, Any]) -> None:
        """Write data in batch mode.

        Args:
            param_dct (dict[str, Any]): Dictionary containing batch write parameters
        """
        ...
