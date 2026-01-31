from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash            import Safe_Str__Cache__File__Cache_Hash
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace                   import Safe_Str__Cache__Namespace
from mgraph_ai_service_cache_client.schemas.cache.store.Schema__Cache__Store__Paths                     import Schema__Cache__Store__Paths
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                                    import Safe_UInt
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                                      import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                         import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now                        import Timestamp_Now
from mgraph_ai_service_cache_client.schemas.cache.zip.safe_str.Safe_Str__Cache__Zip__Operation__Message import Safe_Str__Cache__Zip__Operation__Message

class Schema__Cache__Zip__Store__Response(Type_Safe):                                   # Response after storing zip file
    cache_id         : Cache_Id                                            = None       # Generated ID for this zip entry
    cache_hash       : Safe_Str__Cache__File__Cache_Hash                   = None       # Hash of the zip content
    namespace        : Safe_Str__Cache__Namespace                                       # Namespace where stored
    paths            : Schema__Cache__Store__Paths                                      # Storage paths by type
    size             : Safe_UInt                                                        # Size in bytes
    file_count       : Safe_UInt                                                        # Number of files in zip
    stored_at        : Timestamp_Now                                                    # When stored
    error_type       : Safe_Str__Id                                         = None      # Error classification
    error_message    : Safe_Str__Cache__Zip__Operation__Message             = None      # Human-readable error
    success          : bool                                                             # Operation success status



