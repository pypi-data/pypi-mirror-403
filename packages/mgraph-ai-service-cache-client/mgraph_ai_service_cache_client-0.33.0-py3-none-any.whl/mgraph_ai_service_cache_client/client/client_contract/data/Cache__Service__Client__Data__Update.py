# ═══════════════════════════════════════════════════════════════════════════════
# Cache Service Client - Data Update Operations
# Update existing data files under cache entries
# ═══════════════════════════════════════════════════════════════════════════════

from typing                                                                                       import Any, Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests          import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                              import Type_Safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path                 import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                                import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                   import Safe_Str__Id
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                    import type_safe
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Update__Response      import Schema__Cache__Data__Update__Response


class Cache__Service__Client__Data__Update(Type_Safe):                                         # Client for updating data files
    requests : Cache__Service__Client__Requests

    # ═══════════════════════════════════════════════════════════════════════════
    # String Update Operations
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def data__update_string__with__id(self,
                                      cache_id     : Cache_Id    ,
                                      namespace    : Safe_Str__Id,
                                      data_file_id : Safe_Str__Id,
                                      body         : str
                                 ) -> Schema__Cache__Data__Update__Response:                      # Update string data file by id

        path   = f"/{namespace}/cache/{cache_id}/data/update/string/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None

    @type_safe
    def data__update_string__with__id_and_key(self,
                                              cache_id     : Cache_Id             ,
                                              namespace    : Safe_Str__Id         ,
                                              data_key     : Safe_Str__File__Path ,
                                              data_file_id : Safe_Str__Id         ,
                                              body         : str
                                         ) -> Schema__Cache__Data__Update__Response:              # Update string data file by id and key

        path   = f"/{namespace}/cache/{cache_id}/data/update/string/{data_key}/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # JSON Update Operations
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def data__update_json__with__id(self,
                                    cache_id     : Cache_Id    ,
                                    namespace    : Safe_Str__Id,
                                    data_file_id : Safe_Str__Id,
                                    body         : Dict
                               ) -> Schema__Cache__Data__Update__Response:                        # Update JSON data file by id

        path   = f"/{namespace}/cache/{cache_id}/data/update/json/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None

    @type_safe
    def data__update_json__with__id_and_key(self,
                                            cache_id     : Cache_Id             ,
                                            namespace    : Safe_Str__Id         ,
                                            data_key     : Safe_Str__File__Path ,
                                            data_file_id : Safe_Str__Id         ,
                                            body         : Dict
                                       ) -> Schema__Cache__Data__Update__Response:                # Update JSON data file by id and key

        path   = f"/{namespace}/cache/{cache_id}/data/update/json/{data_key}/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # Binary Update Operations
    # ═══════════════════════════════════════════════════════════════════════════

    @type_safe
    def data__update_binary__with__id(self,
                                      cache_id     : Cache_Id    ,
                                      namespace    : Safe_Str__Id,
                                      data_file_id : Safe_Str__Id,
                                      body         : bytes
                                 ) -> Schema__Cache__Data__Update__Response:                      # Update binary data file by id

        path   = f"/{namespace}/cache/{cache_id}/data/update/binary/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None

    @type_safe
    def data__update_binary__with__id_and_key(self,
                                              cache_id     : Cache_Id             ,
                                              namespace    : Safe_Str__Id         ,
                                              data_key     : Safe_Str__File__Path ,
                                              data_file_id : Safe_Str__Id         ,
                                              body         : bytes
                                         ) -> Schema__Cache__Data__Update__Response:              # Update binary data file by id and key

        path   = f"/{namespace}/cache/{cache_id}/data/update/binary/{data_key}/{data_file_id}"
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )

        if result.status_code == 200:
            return Schema__Cache__Data__Update__Response.from_json(result.json())
        return None