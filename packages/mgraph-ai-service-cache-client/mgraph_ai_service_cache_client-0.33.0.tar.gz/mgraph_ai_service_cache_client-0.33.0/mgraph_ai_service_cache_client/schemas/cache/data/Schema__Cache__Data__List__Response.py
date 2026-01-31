from typing                                                                            import List
from osbot_utils.type_safe.Type_Safe                                                   import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path      import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                     import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id        import Safe_Str__Id
from osbot_utils.type_safe.primitives.core.Safe_UInt                                   import Safe_UInt
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__File__Info import Schema__Cache__Data__File__Info



class Schema__Cache__Data__List__Response(Type_Safe):
    cache_id    : Cache_Id                              = None                      # Parent cache entry ID
    namespace   : Safe_Str__Id                          = None                      # Cache namespace
    data_key    : Safe_Str__File__Path                  = None                      # Filter path (if specified)
    file_count  : Safe_UInt                             = 0                         # Number of data files found
    files       : List[Schema__Cache__Data__File__Info] = None                      # List of data file info
    total_size  : Safe_UInt                             = 0                         # Total size of all files in bytes