from typing                                                                                 import List
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key  import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id   import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace       import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                        import Safe_UInt
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path           import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now            import Timestamp_Now
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id             import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type              import Enum__Cache__Data_Type


class Schema__Cache__Data__Store__Response(Type_Safe):
    cache_id           : Cache_Id                               = None
    data_files_created : List[Safe_Str__File__Path]             = None
    data_key           : Safe_Str__Cache__File__Data_Key        = None
    data_type          : Enum__Cache__Data_Type                 = None          # Type: 'string', 'json', or 'binary'
    extension          : Safe_Str__Id                           = None
    file_id            : Safe_Str__Cache__File__File_Id         = None
    file_size          : Safe_UInt                              = None          # Size in bytes
    namespace          : Safe_Str__Cache__Namespace             = None
    timestamp          : Timestamp_Now
