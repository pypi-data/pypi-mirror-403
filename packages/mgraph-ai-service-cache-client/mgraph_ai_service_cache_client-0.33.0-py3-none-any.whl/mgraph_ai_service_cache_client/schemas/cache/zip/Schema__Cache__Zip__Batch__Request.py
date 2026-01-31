from typing                                                                          import List
from osbot_utils.type_safe.Type_Safe                                                 import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                   import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id      import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.consts__Cache_Service              import DEFAULT_CACHE__NAMESPACE
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy import Enum__Cache__Store__Strategy
from mgraph_ai_service_cache_client.schemas.cache.zip.Schema__Zip__Batch__Operation  import Schema__Zip__Batch__Operation


class Schema__Cache__Zip__Batch__Request(Type_Safe):                                        # Request for batch zip operations
    atomic       : bool                                = True                               # All-or-nothing execution
    cache_id     : Cache_Id                            = None                               # ID of the zip file to operate on
    namespace    : Safe_Str__Id                        = DEFAULT_CACHE__NAMESPACE           # Namespace for isolation
    strategy     : Enum__Cache__Store__Strategy        = None                               # How to save result
    operations   : List[Schema__Zip__Batch__Operation]                                      # List of operations to perform