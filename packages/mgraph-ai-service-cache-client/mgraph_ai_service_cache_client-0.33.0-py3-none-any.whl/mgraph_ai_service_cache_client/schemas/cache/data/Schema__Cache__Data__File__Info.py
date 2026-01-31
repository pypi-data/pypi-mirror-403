from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id     import Safe_Str__Id
from osbot_utils.type_safe.primitives.core.Safe_UInt                                import Safe_UInt
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type      import Enum__Cache__Data_Type


class Schema__Cache__Data__File__Info(Type_Safe):
    data_file_id : Safe_Str__Id             = None                                  # Data file identifier
    data_key     : Safe_Str__File__Path     = None                                  # Hierarchical path (if any)
    data_type    : Enum__Cache__Data_Type   = None                                  # Type of data (STRING, JSON, BINARY)
    file_path    : Safe_Str__File__Path     = None                                  # Full storage path
    file_size    : Safe_UInt                = None                                  # Size in bytes
    extension    : Safe_Str__Id             = None                                  # File extension (json, txt, bin) # todo: review this attribute, since it looks redundant (since at the moment there is almost a 1-to-1 mapping between data_type and extension