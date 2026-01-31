from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe


class Cache__Service__Client__Info(Type_Safe):
    requests : Cache__Service__Client__Requests

    def health(self) -> Dict:                              # Auto-generated from endpoint get__health
                                                                                    # Build path
        path = "/info/health"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(method = "GET",
                                       path   = path,
                                       body   = body)
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def server(self) -> Dict:                              # Auto-generated from endpoint get__server
                                                                                    # Build path
        path = "/info/server"
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

    def status(self) -> Dict:                              # Auto-generated from endpoint get__status
                                                                                    # Build path
        path = "/info/status"
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
    def versions(self) -> Dict:                              # Auto-generated from endpoint get__versions
        # Build path
        path = "/info/versions"
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
