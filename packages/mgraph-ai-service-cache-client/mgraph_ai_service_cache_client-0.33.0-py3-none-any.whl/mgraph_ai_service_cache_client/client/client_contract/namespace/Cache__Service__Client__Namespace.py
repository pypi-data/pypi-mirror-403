from typing                                                                                    import Dict, List
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests       import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Hash   import Safe_Str__Cache__File__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                             import Cache_Id
from osbot_utils.type_safe.Type_Safe                                                           import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                import Safe_Str__Id
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__List                          import Type_Safe__List
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                 import type_safe


class Cache__Service__Client__Namespace(Type_Safe):
    requests : Cache__Service__Client__Requests

    @type_safe
    def cache_hashes(self,
                     namespace: Safe_Str__Id
                ) -> List[Safe_Str__Cache__File__Cache_Hash]:
                                                                                    # Build path
        path = f"/{namespace}/file-hashes"                                          # todo: BUG: rename file_hashes to cache_hashes     (after client refactor)
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )

        if result.status_code == 200:
            cache_hashes = Type_Safe__List(expected_type=Safe_Str__Cache__File__Cache_Hash)
            cache_hashes.extend(result.json())
            return cache_hashes
        return []

    @type_safe
    def cache_ids(self,
                  namespace: Safe_Str__Id
             ) -> List[Cache_Id]:
                                                                                    # Build path
        path = f"/{namespace}/file-ids"                                             # todo: BUG: rename file_ids to cache_ids     (after client refactor)
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path,
                                       body   = body)

        if result.status_code == 200:
            return result.json()
        else:
            return None

    def stats(self, namespace: str) -> Dict:                              # Auto-generated from endpoint get__stats
                                                                                    # Build path
        path = f"/{namespace}/stats"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path,
                                       body   = body)
        if result.status_code == 200:
            return result.json()
        else:
            return None