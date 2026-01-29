"""PySpark utility functions for common operations.

Provides helper functions for data transformation, configuration building,
and Spark session setup for S3A and other filesystem operations.
"""

import logging
from typing import Any
from pyspark import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, year, month, hour, trim, concat, lpad
from pyspark.sql.types import StructType, StringType, TimestampNTZType, IntegerType

from mynk_etl.utils.common.constants import Constants
from mynk_etl.utils.common.genUtils import param_init


logger = logging.getLogger(__name__)


def colTrim(df: DataFrame) -> DataFrame:
    """Trim whitespace from all string columns in DataFrame.

    Args:
        df (DataFrame): Input DataFrame with string columns

    Returns:
        DataFrame: DataFrame with trimmed string columns
    """
    for i in [field.name for field in df.schema.fields if isinstance(field.dataType, StringType)]:
        df = df.withColumn(i, trim(col(i)))

    return df


def dateTimePartition(nonPartDF: DataFrame, datetimeCol: str) -> DataFrame:
    """Add temporal partition columns (year, month, hour) based on datetime column.

    Converts the datetime column to TimestampNTZType and creates partition columns:
    - year: Four-digit year
    - reporting_month: Year-month in YYYYMM format (zero-padded)
    - hour: Hour of day (0-23)

    Args:
        nonPartDF (DataFrame): Input DataFrame with datetime column
        datetimeCol (str): Name of the datetime column to partition by

    Returns:
        DataFrame: DataFrame with added partition columns
    """
    
    nonPartDF = nonPartDF.withColumn(datetimeCol, col(datetimeCol).cast(TimestampNTZType()).cast(StringType()))
    partDF = nonPartDF.withColumn("year", year(col(datetimeCol)))\
    .withColumn("reporting_month", concat(year(col(datetimeCol)), lpad(month(col(datetimeCol)), 2, "0")).cast(IntegerType()))\
    .withColumn("hour", hour(col(datetimeCol)))

    return partDF


def writerConfig(key) -> dict[str, Any]:
    """Build write configuration dictionary from configuration files.

    Reads configuration for the specified key and builds a dictionary containing
    all parameters needed for data writing operations (mode, options, partitioning, etc.).

    Args:
        key (str): Configuration key in format 'table_group.table_name'

    Returns:
        dict[str, Any]: Configuration dictionary with write parameters including:
            - type: Write type (Streaming/NonStream)
            - partcols: Partition columns (optional)
            - clusteredBy: Clustering specification (optional)
            - dbName: Database name
            - mode: Write mode (append/create/overwrite)
            - Opts: Additional write options
            - triggering: Processing interval for streaming (if applicable)
            - timeout: Termination timeout for streaming (if applicable)
            - checkpointLocation: Checkpoint path for streaming (if applicable)
    """
    prop_key, conf_dict, prop_dict = param_init(key)
    typeOfData = prop_dict['type']

    wrt_dct = dict()
    wrt_dct['type'] = prop_dict['type']
    wrt_dct['partcols'] = prop_dict.get('partcols', None)
    wrt_dct['clusteredBy'] = prop_dict.get('clusteredBy', None)
    wrt_dct['dbName'] = conf_dict['dbName']

    typeOfOps_dict = Constants.INFRA_CFG.value[typeOfData]['common']
    wrt_dct['mode'] = typeOfOps_dict['mode']
    wrt_dct['Opts'] = Constants.INFRA_CFG.value[typeOfData]['Opts']

    if typeOfData == 'Streaming':
        wrt_dct['triggering'] = typeOfOps_dict['triggering']
        wrt_dct['timeout'] = typeOfOps_dict['timeout']
        wrt_dct['checkpointLocation'] = "s3a://" + typeOfOps_dict['checkpointLocation'] + prop_key

    return wrt_dct


def emptyDF(spark: SparkSession) -> DataFrame:
    """Create an empty DataFrame with no schema.

    Args:
        spark (SparkSession): Active Spark session

    Returns:
        DataFrame: Empty DataFrame with empty schema
    """
    empty_schema = StructType([])
    empty_df = spark.createDataFrame([], empty_schema)
    return empty_df


def s3aSparkConfig(spark_context: SparkContext) -> None:
    """Configure Spark context for S3A filesystem operations.

    Sets up Hadoop configuration for S3A to connect to S3-compatible storage
    (e.g., MinIO) with credentials, endpoint, and connection settings.

    Args:
        spark_context (SparkContext): Spark context to configure
    """
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.access.key", Constants.MINIO.value["user"]) # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.secret.key", Constants.MINIO.value["pass"]) # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.endpoint", Constants.MINIO.value["endpoint"]) # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false") # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true") # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.attempts.maximum", "1") # type: ignore
    spark_context._jsc.hadoopConfiguration().set("fs.s3a.connection.establish.timeout", "5000") # type: ignore