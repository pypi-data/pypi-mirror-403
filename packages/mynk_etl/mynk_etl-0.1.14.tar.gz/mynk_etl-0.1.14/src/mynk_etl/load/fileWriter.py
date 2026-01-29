# from typing import Any
# from attrs import define, field
# from .load import Load

# from pyspark.sql import DataFrame

# from utils.confs import varInit, param_init, fetch_conf

# @define(kw_only=True)
# class FileWriter(Load):
#     df: DataFrame
#     key: str = field(eq=str)

#     def streamWriter(self, param_dct: dict[str, Any]) -> None:
        
#         print(f"Writing file in folder : '{param_dct['path']}'")

#         x = self.df.writeStream.trigger(processingTime=param_dct['triggering']).format(param_dct['format']).outputMode(param_dct['mode'])

#         for k, v in param_dct['Opts'].items():
#             if param_dct['format'] == 'parquet' and k == 'delimiter':
#                 continue
#             else:
#                 x = x.option(k, v)

#         if param_dct['partition'] == 'Y':
#             flWrt = x.partitionBy(param_dct['partcols'].split(',')).start()
#         else:
#             flWrt = x.start()
        
#         flWrt.awaitTermination(timeout=int(param_dct['timeout']))


#     def nonStreamWriter(self, param_dct: dict[str, Any]) -> None:
        
#         print(f"Writing file in folder : '{param_dct['path']}'")
        
#         x = self.df.coalesce(2).write

#         for k, v in param_dct['Opts'].items():
#             if param_dct['format'] == 'parquet' and k == 'delimiter':
#                 continue
#             else:
#                 x = x.option(k, v)
        
#         if param_dct['partition'] == 'Y':
#             x = x.partitionBy(param_dct['partcols'].split(','))
        
#         x.format(param_dct['format']).mode(param_dct['mode'])

    
#     def multiSinkWriter(self, param_dct: dict[str, Any]) -> None:
        
#         print(f"Writing file in folder : '{param_dct['path']}'")
        
#         x = self.df.coalesce(2).write

#         for k, v in param_dct['Opts'].items():
#             if param_dct['format'] == 'parquet' and k == 'delimiter':
#                 continue
#             else:
#                 x = x.option(k, v)
        
#         if param_dct['partition'] == 'Y':
#             x = x.partitionBy(param_dct['partcols'].split(','))
        
#         x.format(param_dct['format']).mode(param_dct['mode'])
 

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
#         typeOfOps_dict = varInit(fetch_conf()[typeOfData]['common'])   
#         wrt_dct['mode'] = typeOfOps_dict['mode']
#         wrt_dct['Opts'] = varInit(fetch_conf()[typeOfData]['Opts'])
#         wrt_dct['Opts']['path'] = wrt_dct['hdfsPath'] + varInit(fetch_conf()[typeOfData]['Opts'])['path'] + prop_key
#         wrt_dct['format'] = varInit(fetch_conf()[typeOfData]['File'])['format']

#         if typeOfData == 'Streaming':
#             wrt_dct['triggering'] = typeOfOps_dict['triggering']
#             wrt_dct['timeout'] = typeOfOps_dict['timeout']
#             wrt_dct['checkpointLocation'] = wrt_dct['hdfsPath'] + typeOfOps_dict['checkpointLocation'] + prop_key

#         return self.__writerType[typeOfData](self, wrt_dct)