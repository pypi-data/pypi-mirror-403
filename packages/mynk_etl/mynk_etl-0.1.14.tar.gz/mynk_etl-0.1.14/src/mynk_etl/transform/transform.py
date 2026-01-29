"""Abstract base class for data transformation operations.

This module defines the Transform abstract base class that serves as an interface
for implementing various data transformation strategies.
"""

from attrs import define, field, validators
from abc import ABC

from pyspark.sql import DataFrame, SparkSession


@define(kw_only=True)
class Transform(ABC):
    """Abstract base class for data transformation.

    Provides interface for transforming PySpark DataFrames with various
    data cleaning and enrichment operations.

    Attributes:
        spark (SparkSession): PySpark session for data operations
        df (DataFrame): DataFrame to be transformed
    """
    spark: SparkSession = field(validator=validators.instance_of(SparkSession))
    df: DataFrame = field(validator=validators.instance_of(DataFrame))
    