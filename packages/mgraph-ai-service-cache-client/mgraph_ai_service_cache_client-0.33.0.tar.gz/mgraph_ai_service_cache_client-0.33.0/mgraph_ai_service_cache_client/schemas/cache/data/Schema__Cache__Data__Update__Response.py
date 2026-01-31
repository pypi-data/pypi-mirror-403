from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                  import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id     import Safe_Str__Id
from osbot_utils.type_safe.primitives.core.Safe_UInt                                import Safe_UInt
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type      import Enum__Cache__Data_Type


class Schema__Cache__Data__Update__Response(Type_Safe):
    success      : bool                     = False                                 # Whether the update succeeded
    cache_id     : Cache_Id                 = None                                  # Parent cache entry ID
    namespace    : Safe_Str__Id             = None                                  # Cache namespace
    data_type    : Enum__Cache__Data_Type   = None                                  # Type of data (STRING, JSON, BINARY)
    data_key     : Safe_Str__File__Path     = None                                  # Optional hierarchical path
    data_file_id : Safe_Str__Id             = None                                  # Data file identifier
    file_path    : Safe_Str__File__Path     = None                                  # Full path to updated file
    file_size    : Safe_UInt                = None                                  # Size of updated file in bytes