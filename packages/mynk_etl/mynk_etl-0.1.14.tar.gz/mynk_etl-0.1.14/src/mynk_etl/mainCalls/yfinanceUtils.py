"""Orchestration functions for yfinance data processing.

This module coordinates the complete ETL pipeline for financial data extraction
from Kafka, transformation, and loading to Iceberg tables.
"""

import logging
from mynk_etl.extract.kafkaExtract import KafkaExtract
from mynk_etl.transform.yfinance.tickTransform import TickTransform
from mynk_etl.load.icebergWriter import IcebergWriter
from mynk_etl.sparkUtils.sparkInit import sparkIcebergKafka   


logger = logging.getLogger(__name__)


def writeYfData(key: str) -> None:
    """Execute complete ETL pipeline for yfinance data.

    Orchestrates the following steps:
    1. Initialize Spark session with Iceberg and Kafka support
    2. Extract financial tick data from Kafka topics
    3. Transform data (clean and add temporal partitions)
    4. Load data to Iceberg table
    5. Gracefully shutdown Spark session

    Args:
        key (str): Configuration key in format 'table_group.table_name' that
                   specifies which data source and destination to use

    Raises:
        Exception: Any exception during extraction, transformation, or loading
                   is logged and propagated
    """
    logger.info("Spark Session Initionlizing...")
    spark = sparkIcebergKafka(key)
    logger.info("Spark Session Initionlized")
    
    logger.info(f"Fetching data from Kafka for key: {key}")
    df = KafkaExtract(spark=spark, key=key).getData()
    logger.info(f"Fetched data from Kafka for key: {key}")
    df = TickTransform(spark=spark, df=df).transformTickData()
    logger.info(f"Writing data to Iceberg for key: {key}")
    IcebergWriter(spark=spark, df=df, key=key).writer()
    # df.show(5, False)
    # df.printSchema()

    spark.stop()