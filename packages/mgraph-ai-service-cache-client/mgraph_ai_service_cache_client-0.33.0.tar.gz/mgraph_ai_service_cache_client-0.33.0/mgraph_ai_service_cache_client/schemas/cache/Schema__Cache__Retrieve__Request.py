from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash    import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id


class Schema__Cache__Retrieve__Request(Type_Safe):  # Request schema for retrieving cache data
    cache_hash      : Safe_Str__Cache_Hash  = None
    cache_id        : Cache_Id           = None
    include_data    : bool                  = True
    include_metadata: bool                  = True
    include_config  : bool                  = True