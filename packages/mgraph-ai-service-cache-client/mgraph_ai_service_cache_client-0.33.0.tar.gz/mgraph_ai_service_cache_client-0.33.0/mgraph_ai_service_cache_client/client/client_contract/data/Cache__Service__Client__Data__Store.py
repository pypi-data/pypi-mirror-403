from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests    import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Data_Key  import Safe_Str__Cache__File__Data_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id   import Safe_Str__Cache__File__File_Id
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace       import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id             import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.data.Schema__Cache__Data__Store__Response import Schema__Cache__Data__Store__Response
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Namespace      import Safe_Str__Namespace
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                              import type_safe


class Cache__Service__Client__Data__Store(Type_Safe):
    requests : Cache__Service__Client__Requests

    def data__store_binary(self,
                           cache_id : str,
                           namespace: str,
                           body     :bytes
                      ) -> Schema__Cache__Data__Store__Response:                    # Auto-generated from endpoint post__data__store_binary
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/binary"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())          # Return response data
        else:
            return None


    def data__store_binary__with__id(self,
                                     cache_id    : str ,
                                     namespace   : str ,
                                     data_file_id: str ,
                                     body        :bytes
                                ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_binary__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/binary/{data_file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())              # Return response data
        else:
            return None


    def data__store_binary__with__id_and_key(self,
                                             cache_id    : str ,
                                             namespace   : str ,
                                             data_key    : str ,
                                             data_file_id: str ,
                                             body        : bytes
                                        ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_binary__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/binary/{data_key}/{data_file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())         # Return response data
        else:
            return None

    def data__store_json(self,
                         cache_id : str,
                         namespace: str,
                         body     :dict
                    ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_json
                                                                                    # Build path
        #path = f"/{{namespace}}/cache/{{cache_id}}/data/store/json"
        path = f"/{namespace}/cache/{cache_id}/data/store/json"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())              # Return response data
        else:
            return None


    def data__store_json__with__id(self,
                                   cache_id: str,
                                   namespace: str,
                                   data_file_id: str,
                                   body:dict) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_json__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/json/{data_file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())                # Return response data
        else:
            return None

    @type_safe
    def data__store_json__with__id_and_key(self,
                                           cache_id    : Cache_Id,
                                           namespace   : Safe_Str__Cache__Namespace,
                                           data_key    : Safe_Str__Cache__File__Data_Key,
                                           data_file_id: Safe_Str__Cache__File__File_Id,
                                           body        : dict
                                      ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_json__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/json/{data_key}/{data_file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())          # Return response data
        else:
            return None

    def data__store_string(self, cache_id: str,
                           namespace: Safe_Str__Id,
                           body:str) -> Schema__Cache__Data__Store__Response:
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/store/string"
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())
        else:
            return None

    def data__store_string__with__id(self, cache_id     : str,
                                           namespace    : Safe_Str__Id,
                                           data_file_id : Safe_Str__Id,
                                           body         : str
                                     ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_string__with__id

        path = f"/{namespace}/cache/{cache_id}/data/store/string/{data_file_id}"      # Build path
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())  # Return response data
        else:
            return None

    def data__store_string__with__id_and_key(self, cache_id     : Cache_Id                         ,
                                                   namespace    : Safe_Str__Namespace              ,
                                                   data_key     : Safe_Str__Cache__File__Data_Key  ,
                                                   data_file_id : Safe_Str__Cache__File__File_Id   ,
                                                   body: str
                                             ) -> Schema__Cache__Data__Store__Response:                              # Auto-generated from endpoint post__data__store_string__with__id_and_key

        path = f"/{namespace}/cache/{cache_id}/data/store/string/{data_key}/{data_file_id}"  # Build path
                                                                                             # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path   ,
                                       body   = body   )
        if result.status_code == 200:
            return Schema__Cache__Data__Store__Response.from_json(result.json())                         # Return response data
        else:
            return None