# from typing import Any
# from attrs import define, field
# from src import CURRENT_DATE
# from .load import Load
# from utils.confs import varInit, param_init, fetch_conf

# from pyspark.sql import DataFrame
# from pyspark.sql.functions import col


# @define(kw_only=True)
# class RDBMSWriter(Load):
#     df: DataFrame
#     key: str = field(eq=str)

    
#     def streamWriter(self, param_dct: dict[str, Any]) -> None:

#         table = self.key.split('.')[1].lower()
        
#         print(f"Writing Table : {param_dct['dbName']}.{table}")

#         x = self.df.writeStream.trigger(processingTime=param_dct['triggering'])

#         for k, v in param_dct['Opts'].items():
#             x = x.option(k, v)

#         if param_dct['partition'] == 'Y':
#             x.toTable(f"nessie.{param_dct['dbName']}.{table}", format="iceberg", outputMode=param_dct['mode'], partitionBy=param_dct['partcols'].split(',')).awaitTermination(timeout=int(param_dct['timeout']))
#         else:
#             x.toTable(f"nessie.{param_dct['dbName']}.{table}", format="iceberg", outputMode=param_dct['mode']).awaitTermination(timeout=int(param_dct['timeout']))
        

#     def nonStreamWriter(self, param_dct: dict[str, Any]) -> None:

#         table = self.key.split('.')[1].lower()
        
#         print(f"Writing Table : {param_dct['dbName']}.{table}")
        
#         x = self.df.writeTo(f"nessie.{param_dct['dbName']}.{table}").using("iceberg")
        
#         if param_dct['partition'] == 'Y':
#             x = x.partitionedBy(*[col(x) for x in param_dct['partcols'].split(",")])
        
#         __OPS_TYPE = {
#             "create" : x.createOrReplace(),
#             "append" : x.append(),
#             "overwrite" : x.overwritePartitions()
#         }

#         __OPS_TYPE[param_dct['mode']]
          

#     def multiSinkWriter(self, param_dct: dict[str, Any]) -> None:
        
#         table = self.key.split('.')[1].lower()

#         print(f"Writing Table : {param_dct['dbName']}.{table}")

#         x = self.df.writeTo(f"nessie.{param_dct['dbName']}.{table}").using("iceberg")
        
#         if param_dct['partition'] == 'Y':
#             x = x.partitionedBy(*[col(x) for x in param_dct['partcols'].split(",")])

#         x.append()


#     __writerType = {
#         "NonStream": nonStreamWriter,
#         "Streaming": streamWriter,
#         "MultiSink": multiSinkWriter
#     }

#     def writer(self, typeOfOpr=None) -> None:

#         conf_key, prop_key, conf_dict, prop_dict = param_init(self.key)

#         typeOfData = typeOfOpr or prop_dict['type']

#         wrt_dct = {}
#         wrt_dct['partition'] = prop_dict['partition'].upper()
#         if wrt_dct['partition'] == 'Y':
#             wrt_dct['partcols'] = prop_dict['partcols']
#         wrt_dct['dbName'] = conf_dict['dbName']

#         wrt_dct['hdfsPath'] = varInit(fetch_conf()['SparkParam']['common'])['hdfsPath']   
#         wrt_dct['mode'] = varInit(fetch_conf()[typeOfData]['common'])['mode']
#         wrt_dct['Opts'] = varInit(fetch_conf()[typeOfData]['Opts'])

#         if typeOfData == 'Streaming':
#             wrt_dct['triggering'] = varInit(fetch_conf()[typeOfData]['common'])['triggering']
#             wrt_dct['timeout'] = varInit(fetch_conf()[typeOfData]['common'])['timeout']
#             wrt_dct['Opts']['checkpointLocation'] = wrt_dct['hdfsPath'] + wrt_dct['Opts']['checkpointLocation'] + CURRENT_DATE + "-" + prop_key

#         return self.__writerType[typeOfData](self, wrt_dct)