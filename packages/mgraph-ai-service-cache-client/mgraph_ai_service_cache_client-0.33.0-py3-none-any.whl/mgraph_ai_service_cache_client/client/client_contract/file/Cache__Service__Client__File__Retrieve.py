from typing                                                                              import Dict, Union
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from mgraph_ai_service_cache_client.schemas.cache.file.Schema__Cache__File__Metadata     import Schema__Cache__File__Metadata
from mgraph_ai_service_cache_client.schemas.cache.file.Schema__Cache__File__Refs         import Schema__Cache__File__Refs
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                           import type_safe
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Binary__Reference       import Schema__Cache__Binary__Reference
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Metadata                import Schema__Cache__Metadata
from mgraph_ai_service_cache_client.schemas.cache.Schema__Cache__Retrieve__Success       import Schema__Cache__Retrieve__Success


class Cache__Service__Client__File__Retrieve(Type_Safe):
    requests : Cache__Service__Client__Requests                                 # Transport received from client


    @type_safe
    def retrieve__cache_id(self,
                           cache_id: str,
                           namespace: str
                      ) -> Union[Schema__Cache__Retrieve__Success, Schema__Cache__Binary__Reference]:           # todo: refactor to one class                        # Auto-generated from endpoint get__retrieve__cache_id
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path,
                                       body   = body)
        if result.status_code == 200:
            result_json = result.json()

            if result_json.get('detail',{}).get('error_type'):          # todo: create a better way to handle these errors
                return None
            if result_json.get('binary_url'):
                return Schema__Cache__Binary__Reference.from_json(result_json)
            else:
                return Schema__Cache__Retrieve__Success.from_json(result_json)
        else:
            return None

    def retrieve__cache_id__config(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__cache_id__config
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}/config"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.json()
        return None

    def retrieve__cache_id__metadata(self, cache_id: str, namespace: str) -> Schema__Cache__File__Metadata:                              # Auto-generated from endpoint get__retrieve__cache_id__metadata
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}/metadata"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
                                                                                    # Return response data
        if result.status_code == 200:
            if result.json():
                return Schema__Cache__File__Metadata.from_json(result.json())
        return None

    def retrieve__cache_id__refs(self, cache_id: str, namespace: str) -> Schema__Cache__File__Refs:                              # Auto-generated from endpoint get__retrieve__cache_id__refs
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}/refs"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return Schema__Cache__File__Refs.from_json(result.json())
        return None


    def retrieve__cache_id__refs__all(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__cache_id__refs__all
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}/refs/all"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.json()
        return None

    def retrieve__hash__cache_hash(self,
                                   cache_hash: str,
                                   namespace : str
                              ) -> Union[Schema__Cache__Retrieve__Success, Schema__Cache__Binary__Reference]:           # todo: refactor to one class                    # Auto-generated from endpoint get__retrieve__hash__cache_hash
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        result_json = result.json()                                   # todo: refactor this code with the one from retrieve__cache_id (since it is the same)

        if result_json.get('detail',{}).get('error_type'):          # todo: create a better way to handle these errors
            return None
        if result_json.get('binary_url'):
            return Schema__Cache__Binary__Reference.from_json(result_json)
        else:
            return Schema__Cache__Retrieve__Success.from_json(result_json)

    def retrieve__cache_id__string(self, cache_id: str, namespace: str) -> str:                              # Auto-generated from endpoint get__retrieve__cache_id__string
                                                                                    # Build path
        #path = f"/{namespace}}/retrieve/{cache_id}}/string"                      # todo: BUG: used {{
        path = f"/{namespace}/retrieve/{cache_id}/string"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.text
        return None

    def retrieve__cache_id__json(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__cache_id__json
                                                                                    # Build path
        path = f"/{namespace}/retrieve/{cache_id}/json"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return result.json()
        return None

    def retrieve__cache_id__binary(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__cache_id__binary
                                                                                    # Build path
        #path = f"/{{namespace}}/retrieve/{{cache_id}}/binary"                      # todo: BUG: used {{
        path = f"/{namespace}/retrieve/{cache_id}/binary"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.content                                               #       and since this is binary we need to return the result.content
        return None

    def retrieve__hash__cache_hash__string(self, cache_hash: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__string
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/string"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return result.text
        return None

    def retrieve__hash__cache_hash__json(self, cache_hash: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__json
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/json"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return result.json()
        return None

    def retrieve__hash__cache_hash__binary(self, cache_hash: str, namespace: str) -> Dict:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__binary
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/binary"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.content
        return None

    def retrieve__hash__cache_hash__metadata(self,
                                             cache_hash: str,
                                             namespace: str
                                        ) -> Schema__Cache__Metadata:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__string
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/metadata"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return Schema__Cache__Metadata.from_json(result.json())
        return None

    # todo: rename this should be just retrieve__hash__cache_hash__refs
    def retrieve__hash__cache_hash__refs_hash(self,
                                             cache_hash: str,
                                             namespace: str
                                        ) -> Schema__Cache__Metadata:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__string
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/refs-hash"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return result.json()
        return None

    # todo: refactor main client to return a type_safe class here
    @type_safe
    def retrieve__hash__cache_hash__cache_id(self,
                                             cache_hash: str,
                                             namespace : str
                                        ) -> Dict:                              # Auto-generated from endpoint get__retrieve__hash__cache_hash__string
                                                                                    # Build path
        path = f"/{namespace}/retrieve/hash/{cache_hash}/cache-id"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path ,
                                       body   = body )
        if result.status_code == 200:
            return result.json()
        return None