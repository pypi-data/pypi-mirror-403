from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests


# todo: add a parent .file() class, just like we did for .data()

class Cache__Service__Client__File__Delete(Type_Safe):
    requests : Cache__Service__Client__Requests

    # todo: this should a variation of the Schema__Cache__Delete__Success (which needed refactoring)
    def delete__cache_id(self, cache_id: str, namespace: str) -> Dict:                              # Auto-generated from endpoint delete__delete__cache_id
                                                                                    # Build path
        path = f"/{namespace}/delete/{cache_id}"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "DELETE",
            path   = path,
            body   = body
        )
        if result.status_code == 200:
            return result.json()
        else:
            return None