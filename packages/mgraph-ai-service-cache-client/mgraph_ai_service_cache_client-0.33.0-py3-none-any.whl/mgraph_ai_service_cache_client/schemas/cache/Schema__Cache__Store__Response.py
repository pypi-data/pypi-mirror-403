from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash    import Safe_Str__Cache__File__Cache_Hash
from mgraph_ai_service_cache_client.schemas.cache.store.Schema__Cache__Store__Paths             import Schema__Cache__Store__Paths
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace           import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                              import Cache_Id
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                            import Safe_UInt


class Schema__Cache__Store__Response(Type_Safe):
    cache_id   : Cache_Id
    cache_hash : Safe_Str__Cache__File__Cache_Hash
    namespace  : Safe_Str__Cache__Namespace
    paths      : Schema__Cache__Store__Paths                              # Structured paths
    size       : Safe_UInt                                                # Size in bytes