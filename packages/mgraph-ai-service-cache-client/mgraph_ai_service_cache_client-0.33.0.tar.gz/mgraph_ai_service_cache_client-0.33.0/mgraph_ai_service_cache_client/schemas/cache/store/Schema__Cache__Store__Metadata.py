from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash    import Safe_Str__Cache__File__Cache_Hash
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Key     import Safe_Str__Cache__File__Cache_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id       import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace           import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                              import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                 import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now                import Timestamp_Now
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Json__Field_Path   import Safe_Str__Json__Field_Path
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__File_Type                  import Enum__Cache__File_Type
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy            import Enum__Cache__Store__Strategy

# todo: update to correct Cache system types
class Schema__Cache__Store__Metadata(Type_Safe):                                              # Metadata for stored cache entries
    cache_hash       : Safe_Str__Cache__File__Cache_Hash = None                               # Hash of the data
    cache_key        : Safe_Str__Cache__File__Cache_Key  = None                               # Optional semantic key
    cache_id         : Cache_Id                          = None                               # Cache entry ID
    content_encoding : Safe_Str__Id                      = None                               # Optional encoding
    file_id          : Safe_Str__Cache__File__File_Id    = None                               # File ID used for storage
    file_type        : Enum__Cache__File_Type            = None                                # Type: 'json' or 'binary'
    json_field_path  : Safe_Str__Json__Field_Path        = None                                # Field Path used to calculate the hash of a Json object
    namespace        : Safe_Str__Cache__Namespace        = None                                # Namespace
    stored_at        : Timestamp_Now                     = None                                # When stored
    strategy         : Enum__Cache__Store__Strategy      = None                                # Storage strategy used

