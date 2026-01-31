from typing                                                                         import Any
from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                  import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id     import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type      import Enum__Cache__Data_Type


class Schema__Cache__Data__Update__Request(Type_Safe):
    cache_id     : Cache_Id                                                         # Parent cache entry ID
    data         : Any                      = None                                  # Data to update (string, dict, or bytes)
    data_type    : Enum__Cache__Data_Type   = None                                  # Type of data (STRING, JSON, BINARY)
    data_key     : Safe_Str__File__Path     = None                                  # Optional hierarchical path
    data_file_id : Safe_Str__Id             = None                                  # Data file identifier
    namespace    : Safe_Str__Id             = None                                  # Cache namespace