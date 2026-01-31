from typing                                                                              import List
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                     import Safe_UInt
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                       import Cache_Id
from mgraph_ai_service_cache_client.schemas.cache.store.Schema__Cache__Hash__Entry       import Schema__Cache__Hash__Entry


class Schema__Cache__Hash__Reference(Type_Safe):           # Hash-to-ID reference structure
    cache_hash     : Safe_Str__Cache_Hash                  # The hash value
    cache_ids      : List[Schema__Cache__Hash__Entry]      # All cache IDs with this hash
    latest_id      : Cache_Id                           # Most recent cache ID
    total_versions : Safe_UInt