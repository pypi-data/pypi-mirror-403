from typing                                                                              import Dict
from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client__Requests import Cache__Service__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe

class Cache__Service__Client__Set_Cookie(Type_Safe):
    requests : Cache__Service__Client__Requests                                                                  # Reference to main client

    def set_cookie_form(self) -> Dict:                              # Auto-generated from endpoint get__set_cookie_form
                                                                                    # Build path
        path = "/auth/set-cookie-form"
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

    def set_auth_cookie(self) -> Dict:                              # Auto-generated from endpoint post__set_auth_cookie
                                                                                    # Build path
        path = "/auth/set-auth-cookie"
        body = None
                                                                                    # Execute request
        result = self.requests.execute(
            method = "POST",
            path   = path,
            body   = body
        )
                                                                                    # Return response data
        if result.status_code == 200:
            return result.json()
        else:
            return None