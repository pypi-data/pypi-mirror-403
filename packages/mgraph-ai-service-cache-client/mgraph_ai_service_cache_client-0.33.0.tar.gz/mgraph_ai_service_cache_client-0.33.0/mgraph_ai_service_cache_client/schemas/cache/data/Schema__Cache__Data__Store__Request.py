from typing                                                                                 import Union
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key  import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id   import Safe_Str__Cache__File__File_Id
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id
from mgraph_ai_service_cache_client.schemas.cache.consts__Cache_Service                     import DEFAULT_CACHE__NAMESPACE
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type              import Enum__Cache__Data_Type
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Namespace      import Safe_Str__Namespace


class Schema__Cache__Data__Store__Request(Type_Safe):
    cache_id    : Cache_Id                          = None
    data        : Union[str, dict, bytes]           = None                           # Data to store as child
    data_type   : Enum__Cache__Data_Type            = None                           # Type: 'string', 'json', or 'binary'
    data_key    : Safe_Str__Cache__File__Data_Key   = None
    data_file_id: Safe_Str__Cache__File__File_Id    = None
    namespace   : Safe_Str__Namespace               = DEFAULT_CACHE__NAMESPACE