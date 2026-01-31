from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                           import type_safe


class Cache__Service__Client__Data__Retrieve(Type_Safe):
    requests : Cache__Service__Client__Requests

    def data__json__with__id(self, cache_id: str, namespace: str, data_file_id: str) -> Dict:                              # Auto-generated from endpoint get__data__json__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/json/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def data__json__with__id_and_key(self, cache_id: str, namespace: str, data_key: str, data_file_id: str) -> Dict:                              # Auto-generated from endpoint get__data__json__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/json/{data_key}/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.json()
        else:
            return None

    @type_safe
    def data__string__with__id(self,
                               cache_id: str,
                               namespace: str,
                               data_file_id: str
                          ) -> str:                              # Auto-generated from endpoint get__data__string__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/string/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            if result.text:                                                                 # handle case when result.text == '' (which happens when the file doesn't exist)
                return result.text
        return None

    def data__string__with__id_and_key(self,
                                       cache_id: str,
                                       namespace: str,
                                       data_key: str,
                                       data_file_id: str) -> Dict:                              # Auto-generated from endpoint get__data__string__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/string/{data_key}/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
                                                                                    # Return response data
        if result.status_code == 200:
            if result.text:                                                         # handle case when result.text == '' (which happens when the file doesn't exist)
                return result.text
        return None

    def data__binary__with__id(self, cache_id: str, namespace: str, data_file_id: str) -> Dict:                              # Auto-generated from endpoint get__data__binary__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/binary/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:                                                                                       # Return response data
            if result.content:
                return result.content
        return None

    def data__binary__with__id_and_key(self, cache_id: str, namespace: str, data_key: str, data_file_id: str) -> Dict:                              # Auto-generated from endpoint get__data__binary__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/binary/{data_key}/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "GET",
            path   = path,
            body   = body
        )
        if result.status_code == 200:                                                                                       # Return response data
            return result.content
        return None