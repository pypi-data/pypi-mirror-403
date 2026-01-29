"""Application-wide constants and configuration.

This module defines all constants used throughout the ETL pipeline including
Run IDs, configuration references, and system defaults.
"""
from os import getenv
from datetime import datetime
from enum import Enum

from mynk_etl.utils.common.confs import fetch_conf, fetch_prop
from socket import gethostname
from xxhash import xxh32_intdigest

class Constants(Enum):
    """Application constants and runtime configuration.

    Attributes:
        RUN_ID: Unique run identifier based on timestamp and hash
        CURRENT_DATE: Current date in YYYY-MM-DD format
        INFRA_CFG: Infrastructure configuration (Spark, Kafka, Nessie, etc.)
        TBL_CFG: Table configuration from YAML
        SPARK_MASTER: Spark master configuration
        NESSIE: Nessie catalog configuration
        MINIO: MinIO S3-compatible storage configuration
        KAFKA_BROKERS: Kafka broker connection configuration
        KAFKA_SCHEMA_CLIENT: Kafka schema registry configuration
        STOCK_EXCHANGE_SUFFIX: Default suffix for NSE stocks (.NS)
        RECORD_TIMESTAMP_KEY: Column name for record timestamp
    """

    RUN_ID = int(datetime.now().strftime('%Y%m%d')  + str(xxh32_intdigest("pystream" + datetime.now().strftime('%H:%M:%S.%f'))))

    CURRENT_DATE = datetime.today().strftime('%Y-%m-%d')

    ENV = getenv('INFRA_ENV', "DEV")

    INFRA_CFG = fetch_conf()[ENV]

    TBL_CFG = fetch_prop()[ENV]

    SPARK_MASTER = INFRA_CFG['SparkParam']

    NESSIE = INFRA_CFG['Nessie']['conf']

    MINIO = INFRA_CFG['Minio']['conf']

    KAFKA_BROKERS = INFRA_CFG['Kafka']['kafka-broker-conf'] | {'client.id': gethostname()}

    KAFKA_SCHEMA_CLIENT = INFRA_CFG['Kafka']['kafka-schema-client-conf']

    STOCK_EXCHANGE_SUFFIX = ".NS"

    RECORD_TIMESTAMP_KEY = "recordtimestamp"