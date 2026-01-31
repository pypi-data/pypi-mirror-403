from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace    import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                       import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id          import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Update__Response        import Schema__Cache__Update__Response


class Cache__Service__Client__File__Update(Type_Safe):
    requests : Cache__Service__Client__Requests

    def update__string(self,
                       cache_id : Cache_Id   ,
                       namespace: Safe_Str__Id  ,
                       body     : str
                  ) -> Schema__Cache__Update__Response:                            # Update string data in existing cache entry
                                                                                    # Build path
        path = f"/{namespace}/update/{cache_id}/string"
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Update__Response.from_json(result.json())
        else:
            return None

    def update__json(self,
                     cache_id : Cache_Id   ,
                     namespace: Safe_Str__Id  ,
                     body     : dict
                ) -> Schema__Cache__Update__Response:                              # Update JSON data in existing cache entry
                                                                                    # Build path
        path = f"/{namespace}/update/{cache_id}/json"
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Update__Response.from_json(result.json())
        else:
            return None


    def update__binary(self,
                       cache_id : Cache_Id   ,
                       namespace: Safe_Str__Cache__Namespace  ,
                       body     : bytes
                  ) -> Schema__Cache__Update__Response:                            # Update binary data in existing cache entry
                                                                                    # Build path
        path = f"/{namespace}/update/{cache_id}/binary"
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path,
                                       body   = body)
        if result.status_code == 200:
            return Schema__Cache__Update__Response.from_json(result.json())
        else:
            return None
