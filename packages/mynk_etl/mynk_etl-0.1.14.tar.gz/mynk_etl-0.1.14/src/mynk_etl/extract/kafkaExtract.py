"""Kafka-based data extraction module.

This module implements data extraction from Apache Kafka topics, handling both
streaming and batch modes with Avro deserialization support.
"""

import logging
from attrs import define

from pyspark.sql import DataFrame
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.functions import col, expr
from pyspark.sql.types import StringType


from mynk_etl.extract.extract import Extract
from mynk_etl.utils.common.constants import Constants
from mynk_etl.utils.common.genUtils import param_init
from mynk_etl.utils.common.kUtils import get_schema_str
from mynk_etl.utils.logger.logDecor import logtimer, inOutLog


logger = logging.getLogger(__name__)


@define(slots=True)
class KafkaExtract(Extract):
    """Extract data from Kafka topics with Avro schema support.

    Implements streaming and batch extraction from Kafka topics, automatically
    deserializing Avro-encoded messages and casting keys to symbol identifiers.
    """

    @logtimer
    def extractSparkStreamData(self, topic: str) -> DataFrame:
        """_summary_

        Args:
            topic (str): Kafka topic to subscribe.

        Returns:
            DataFrame: Return dataframe using 'spark.readStream' on the topic.
        """
        logging.debug("Reading Kafka Stream....")
        kafka_df = (
            self.spark.readStream.format("kafka")
            .option(
                "kafka.bootstrap.servers",
                Constants.KAFKA_BROKERS.value["bootstrap.servers"],
            )
            .option("subscribe", topic)
            .option("startingOffsets", "earliest")
            .option("kafka.compression.type", "snappy")
            .option("failOnDataLoss", "false")
            .option("mode", "DROPMALFORMED")
            .load()
        )

        logging.debug(f"Fetching schema for the topic : {topic}")
        schema = get_schema_str(topic)
        logging.debug(f"Schema fetched for the topic : {topic}")

        kafka_val_df = kafka_df.withColumn(
            "fixedValue", expr("substring(value, 6, length(value)-5)")
        )

        kafka_val_df = kafka_val_df.select(
            col("key").cast(StringType()).alias("symbol"),
            from_avro(
                col("fixedValue"), schema.schema_str, {"mode": "FAILFAST"}
            ).alias("parsed_value"),
        )
        
        kafka_val_df = kafka_val_df.select("symbol", "parsed_value.*")

        return kafka_val_df

    @logtimer
    def extractSparkData(self, topic: str) -> DataFrame:
        """_summary_

        Args:
            topic (str): Kafka topic to subscribe.

        Returns:
            DataFrame: Return dataframe using 'spark.read' on the topic.
        """
        logging.debug("Reading Kafka Stream in one go")
        kafka_df = (
            self.spark.read.format("kafka")
            .option(
                "kafka.bootstrap.servers",
                Constants.KAFKA_BROKERS.value["bootstrap.servers"],
            )
            .option("subscribe", topic)
            .option("startingOffsets", "earliest")
            .option("kafka.compression.type", "snappy")
            .option("failOnDataLoss", "false")
            .option("mode", "DROPMALFORMED")
            .load()
        )

        logging.debug(f"Fetching schema for the topic : {topic}")
        schema = get_schema_str(topic)
        logging.debug(f"Schema fetched for the topic : {topic}")

        kafka_val_df = kafka_df.withColumn(
            "fixedValue", expr("substring(value, 6, length(value)-5)")
        )

        kafka_val_df = kafka_val_df.select(
            col("key").cast(StringType()).alias("symbol"),
            from_avro(
                col("fixedValue"), schema.schema_str, {"mode": "FAILFAST"}
            ).alias("parsed_value"),
        )
        kafka_val_df = kafka_val_df.select("symbol", "parsed_value.*")

        return kafka_val_df

    __extractType = {"NonStream": extractSparkData, "Streaming": extractSparkStreamData}

    @inOutLog
    def getData(self) -> DataFrame:
        """Extract data from Kafka based on configuration.

        Reads configuration for the extraction operation, creates the necessary
        database schema in Nessie, and returns DataFrame extracted from Kafka
        using the configured extraction type (streaming or batch).

        Returns:
            DataFrame: Extracted data from Kafka topic
        """
        prop_key, conf_dict, prop_dict = param_init(self.key)

        self.spark.sql(
            f"CREATE SCHEMA IF NOT EXISTS nessie.{conf_dict['dbName']}"
        ).show()

        return self.__extractType[prop_dict["type"]](self, prop_key.lower())
