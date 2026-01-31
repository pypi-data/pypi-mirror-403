from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                              import Cache_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key      import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id       import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace           import Safe_Str__Cache__Namespace
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type                  import Enum__Cache__Data_Type


class Schema__Cache__Data__Exists__Response(Type_Safe):
    cache_id     : Cache_Id                                                         # Parent cache entry ID
    data_type    : Enum__Cache__Data_Type                                           # Type of data (STRING, JSON, BINARY)
    data_key     : Safe_Str__Cache__File__Data_Key   = None                         # Optional hierarchical path
    data_file_id : Safe_Str__Cache__File__File_Id    = None                         # Data file identifier
    exists       : bool                                                             # Whether the data file exists
    namespace    : Safe_Str__Cache__Namespace                                       # Cache namespace