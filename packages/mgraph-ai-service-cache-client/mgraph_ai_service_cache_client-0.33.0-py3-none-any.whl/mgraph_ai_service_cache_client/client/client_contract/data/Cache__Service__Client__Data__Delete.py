from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Data_Type           import Enum__Cache__Data_Type


class Cache__Service__Client__Data__Delete(Type_Safe):
    requests : Cache__Service__Client__Requests                                                                   # Reference to main client


    def delete__all__data__files(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint delete__delete__all__data__files
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/delete/all"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "DELETE",
                                       path   = path    ,
                                       body   = body    )
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def delete__all__data__files__with__key(self, cache_id: str, namespace: str, data_key: str) -> Dict:                              # Auto-generated from endpoint delete__delete__all__data__files__with__key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/delete/all/{data_key}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "DELETE",
                                       path   = path    ,
                                       body   = body    )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def delete__data__file__with__id(self, cache_id: str, namespace: str, data_type: Enum__Cache__Data_Type, data_file_id: str) -> Dict:                              # Auto-generated from endpoint delete__delete__data__file__with__id
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/delete/{data_type.value}/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "DELETE",
                                       path   = path    ,
                                       body   = body    )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def delete__data__file__with__id_and_key(self, cache_id: str, namespace: str, data_type: Enum__Cache__Data_Type, data_key: str, data_file_id: str) -> Dict:                              # Auto-generated from endpoint delete__delete__data__file__with__id_and_key
                                                                                    # Build path
        path = f"/{namespace}/cache/{cache_id}/data/delete/{data_type.value}/{data_key}/{data_file_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "DELETE",
                                       path   = path    ,
                                       body   = body    )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.json()
        else:
            return None