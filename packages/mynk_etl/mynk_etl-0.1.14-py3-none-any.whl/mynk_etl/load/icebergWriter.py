"""Iceberg table writer module.

This module implements data writing to Apache Iceberg tables on Nessie,
supporting streaming, batch, and multi-sink write operations.
"""

import logging

from typing import Any
from attrs import define

from pyspark.sql.functions import col

from mynk_etl.load.load import Load
from mynk_etl.sparkUtils.sparkComfunc import writerConfig


logger = logging.getLogger(__name__)


@define(slots=True)
class IcebergWriter(Load):
    """Write data to Apache Iceberg tables on Nessie catalog.

    Supports streaming and batch write operations with support for partitioning,
    clustering, and various write modes (create, append, overwrite).
    """
    
    
    def streamWriter(self, param_dct: dict[str, Any]) -> None:
        """Write streaming DataFrame to Iceberg table.

        Args:
            param_dct (dict[str, Any]): Configuration dictionary containing:
                - dbName: Database name
                - triggering: Processing time interval for triggering
                - Opts: Additional write options
                - mode: Output mode (append/complete/update)
                - timeout: Query termination timeout
                - checkpointLocation: Checkpoint directory path
                - partcols: Optional partition columns
                - clusteredBy: Optional clustering specification

        Raises:
            Exception: If table write operation fails
        """
        table = self.key.split(".")[1].lower()
        logger.info(f"Writing Table : {param_dct['dbName']}.{table}")

        x = self.df.writeStream.trigger(processingTime=param_dct['triggering'])

        for k, v in param_dct['Opts'].items():
            if k != 'path':
                x = x.option(k, v)

        try:
            query = x.toTable(f"nessie.{param_dct['dbName']}.{table}", format="iceberg", outputMode=param_dct['mode'], partitionBy=param_dct.get('partcols',None), checkpointLocation=param_dct['checkpointLocation'], clusteredBy=param_dct.get('clusteredBy', None))
            
            query.awaitTermination(timeout=int(param_dct['timeout']))
            
            logger.info(f" Table : {param_dct['dbName']}.{table} written successfully.")
        except Exception as e:
            logger.error(f"Error writing Table : {param_dct['dbName']}.{table} - {e}")
            raise e


    def nonStreamWriter(self, param_dct: dict[str, Any]) -> None:
        """Write batch DataFrame to Iceberg table.

        Creates new table or appends/overwrites data based on table existence
        and configured write mode.

        Args:
            param_dct (dict[str, Any]): Configuration dictionary containing:
                - dbName: Database name
                - mode: Write mode (create/append/overwrite)
                - partcols: Optional partition columns

        Raises:
            Exception: If table write operation fails
        """
        table = self.key.split(".")[1].lower()
        logger.info(f"Writing Table : {param_dct['dbName']}.{table}")
        
        x = self.df.writeTo(f"nessie.{param_dct['dbName']}.{table}").using("iceberg")
        
        if param_dct.get('partcols', False):
            x = x.partitionedBy(*[col(x) for x in param_dct['partcols']])
        
        __OPS_TYPE = {
            "create" : x.createOrReplace(),
            "append" : x.append(),
            "overwrite" : x.overwritePartitions()
        }

        try:
            if self.spark.catalog.tableExists(f"nessie.{param_dct['dbName']}.{table}"):
                __OPS_TYPE[param_dct['mode']]
            else:
                __OPS_TYPE['create']

            logger.info(f" Table : {param_dct['dbName']}.{table} written successfully.")
        except Exception as e:
            logger.error(f"Error writing Table : {param_dct['dbName']}.{table} - {e}")
            raise e
            
          
    def multiSinkWriter(self, param_dct: dict[str, Any]) -> None:
        """Write DataFrame to multiple Iceberg table sinks.

        Appends data to Iceberg table with optional partitioning configuration.

        Args:
            param_dct (dict[str, Any]): Configuration dictionary containing:
                - dbName: Database name
                - partition: Whether to partition ('Y'/'N')
                - partcols: Comma-separated partition columns if partitioning enabled
        """
        table = self.key.split(".")[1].lower()
        logger.info(f"Writing Table : {param_dct['dbName']}.{table}")

        x = self.df.writeTo(f"nessie.{param_dct['dbName']}.{table}").using("iceberg")
        
        if param_dct['partition'] == 'Y':
            x = x.partitionedBy(*[col(x) for x in param_dct['partcols'].split(",")])

        x.append()


    __writerType = {
        "NonStream": nonStreamWriter,
        "Streaming": streamWriter,
        "MultiSink": multiSinkWriter
    }

    def writer(self) -> None:
        """Execute write operation based on configuration.

        Fetches write configuration and executes the appropriate write method
        (streaming, batch, or multi-sink) based on the configured operation type.
        """
        wrt_dct = writerConfig(self.key)
        logger.info(wrt_dct)

        return self.__writerType[wrt_dct['type']](self, wrt_dct)