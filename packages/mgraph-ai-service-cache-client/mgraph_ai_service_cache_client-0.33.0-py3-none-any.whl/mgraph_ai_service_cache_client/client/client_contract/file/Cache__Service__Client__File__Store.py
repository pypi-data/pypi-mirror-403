from typing                                                                                   import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests      import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Key   import Safe_Str__Cache__File__Cache_Key
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__File_Id     import Safe_Str__Cache__File__File_Id
from osbot_utils.type_safe.Type_Safe                                                          import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id               import Safe_Str__Id
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Store__Response              import Schema__Cache__Store__Response
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy          import Enum__Cache__Store__Strategy
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Json__Field_Path import Safe_Str__Json__Field_Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Namespace        import Safe_Str__Namespace
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                import type_safe

class Cache__Service__Client__File__Store(Type_Safe):
    requests : Cache__Service__Client__Requests                                 # Transport received from client


    def store__string(self, strategy  : Enum__Cache__Store__Strategy,
                            namespace: Safe_Str__Id                 ,
                            body : str
                      ) -> Schema__Cache__Store__Response:                                                    # Auto-generated from endpoint post__store__string
                                                                                    # Build path
        path = f"/{namespace}/{strategy}/store/string"
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.json())                # Return response data
        else:
            return None

    @type_safe
    def store__string__cache_key(self, namespace: str                           ,
                                       strategy : Enum__Cache__Store__Strategy  ,
                                       cache_key: str                           ,
                                       body     : str                           ,
                                       file_id  : str   = ''
                                  ) -> Schema__Cache__Store__Response:                              # Auto-generated from endpoint post__store__string__cache_key
                                                                                    # Build path
        path = f"/{namespace}/{strategy}/store/string/{cache_key}?file_id={file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.json())
        else:
            return None

    def store__json(self, strategy : Enum__Cache__Store__Strategy,
                          namespace: Safe_Str__Id,
                          body     : Dict
                      )-> Schema__Cache__Store__Response:
        path = f"/{namespace}/{strategy}/store/json"                            # Build path
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.text)              # Return response data
        else:
            return None

    @type_safe
    def store__json__cache_key(self,
                               namespace      : Safe_Str__Namespace             ,
                               strategy       : Enum__Cache__Store__Strategy    ,
                               cache_key      : Safe_Str__Cache__File__Cache_Key,
                               body           : dict                            ,
                               file_id        : Safe_Str__Cache__File__File_Id  ,
                               json_field_path: Safe_Str__Json__Field_Path      = ''
                          ) -> Schema__Cache__Store__Response:                          # Auto-generated from endpoint post__store__json__cache_key
                                                                                    # Build path
        path = f"/{namespace}/{strategy}/store/json/{cache_key}?file_id={file_id}&json_field_path={json_field_path}"
                                                                                    # Execute request
        result = self.requests.execute(method = "POST"  ,
                                       path   = path    ,
                                       body   = body    )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.json())                # Return response data
        else:
            return None


    def store__binary(self, strategy : Enum__Cache__Store__Strategy,
                            namespace: Safe_Str__Id                ,
                            body     : bytes
                       ) -> Schema__Cache__Store__Response:
        path  = f"/{namespace}/{strategy}/store/binary"                          # Build path
        result = self.requests.execute(method = "POST",                             # Execute request
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.json())                # Return response data
        else:
            return None

    def store__binary__cache_key(self, namespace: str,
                                       strategy: Enum__Cache__Store__Strategy,
                                       cache_key: str,
                                       body = bytes ,
                                       file_id: str = '') -> Schema__Cache__Store__Response:                              # Auto-generated from endpoint post__store__binary__cache_key
                                                                                    # Build path
        path = f"/{namespace}/{strategy}/store/binary/{cache_key}?file_id={file_id}"
        #body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "POST",
                                       path   = path  ,
                                       body   = body  )
        if result.status_code == 200:
            return Schema__Cache__Store__Response.from_json(result.json())                # Return response data
        else:
            return None
