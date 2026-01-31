from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash import Safe_Str__Cache__File__Cache_Hash
from osbot_utils.type_safe.Type_Safe                                                         import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                           import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id              import Safe_Str__Id



class Schema__Cache__Exists__Response(Type_Safe):                           # Response schema for cache entry existence check
    exists     : bool                                                       # True if entry exists
    cache_id   : Cache_Id                           = None                  # Cache ID that was checked   (if checking by ID)
    cache_hash : Safe_Str__Cache__File__Cache_Hash  = None                  # Cache hash that was checked (if checking by hash)
    namespace  : Safe_Str__Id                                               # Namespace where check was performed