from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe

class Cache__Service__Client__Namespaces(Type_Safe):
    requests : Cache__Service__Client__Requests

    def list(self) -> Dict:
                                                                                    # Build path
        path = f"/namespaces/list"
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
        else:
            return None