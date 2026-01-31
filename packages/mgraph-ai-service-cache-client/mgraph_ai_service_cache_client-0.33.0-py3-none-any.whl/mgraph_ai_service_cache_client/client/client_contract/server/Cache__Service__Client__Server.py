from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe

class Cache__Service__Client__Server(Type_Safe):
    requests : Cache__Service__Client__Requests

    def storage__info(self) -> Dict:                              # Auto-generated from endpoint get__storage__info
                                                                                    # Build path
        path = "/server/storage/info"
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

    def create__test_fixtures(self) -> Dict:                              # Auto-generated from endpoint get__create__test_fixtures
                                                                                    # Build path
        path = "/server/create/test-fixtures"
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